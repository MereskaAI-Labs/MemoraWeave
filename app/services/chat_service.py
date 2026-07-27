import hashlib
import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.core.config import settings
from app.graph.context import GraphContext
from app.repositories.event_repository import EventRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.request_repository import RequestRepository
from app.repositories.thread_lock_repository import ThreadLockRepository
from app.repositories.thread_repository import ThreadRepository
from app.services.errors import (
    ChatProcessingError,
    IdempotencyConflictError,
    RequestAlreadyProcessingError,
    RequestPreviouslyFailedError,
    ThreadNotFoundError,
)
from app.utils.sse import sse_event


class ChatService:
    def __init__(self, db, graph):
        self.db = db
        self.graph = graph
        self.thread_repo = ThreadRepository(db)
        self.message_repo = MessageRepository(db)
        self.event_repo = EventRepository(db)
        self.request_repo = RequestRepository(db)
        self.lock_repo = ThreadLockRepository(db)

    def _make_request_hash(
        self,
        *,
        thread_id: uuid.UUID,
        user_id: uuid.UUID,
        message_text: str,
    ) -> str:
        raw = f"{thread_id}:{user_id}:{message_text}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _extract_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text_value = item.get("text")
                    if text_value:
                        parts.append(str(text_value))
            return "\n".join(part for part in parts if part)

        return str(content or "")
    
    def _json_safe(self, value: Any) -> Any:
        return json.loads(json.dumps(value, default=str, ensure_ascii=False))

    def _extract_messages_from_update(self, update_payload: object) -> list:
        messages: list = []

        if not isinstance(update_payload, dict):
            return messages

        for node_payload in update_payload.values():
            if not isinstance(node_payload, dict):
                continue

            node_messages = node_payload.get("messages")
            if not node_messages:
                continue

            if isinstance(node_messages, list):
                messages.extend(node_messages)
            else:
                messages.append(node_messages)

        return messages

    async def _persist_tool_activity(
        self,
        *,
        thread_id: uuid.UUID,
        user_id: uuid.UUID,
        turn_id: uuid.UUID,
        messages: list,
        seen_tool_call_ids: set[str],
        seen_tool_result_ids: set[str],
        tool_call_names: dict[str, str],
    ) -> tuple[list[str], list[str]]:
        new_tool_call_ids: list[str] = []
        new_tool_result_ids: list[str] = []

        for message in messages:
            if isinstance(message, AIMessage):
                tool_calls = getattr(message, "tool_calls", None) or []

                for tool_call in tool_calls:
                    tool_call_id = str(tool_call.get("id") or "")
                    tool_name = str(tool_call.get("name") or "")
                    tool_args = tool_call.get("args") or {}

                    if not tool_call_id or tool_call_id in seen_tool_call_ids:
                        continue

                    seen_tool_call_ids.add(tool_call_id)
                    tool_call_names[tool_call_id] = tool_name
                    new_tool_call_ids.append(tool_call_id)

                    await self.message_repo.create(
                        thread_id=thread_id,
                        user_id=user_id,
                        role="assistant",
                        turn_id=turn_id,
                        kind="tool_call",
                        tool_name=tool_name,
                        tool_call_id=tool_call_id,
                        content_text=None,
                        content_json={
                            "name": tool_name,
                            "args": self._json_safe(tool_args),
                        },
                    )

                    await self.event_repo.create(
                        thread_id=thread_id,
                        turn_id=turn_id,
                        event_type="tool_call_started",
                        node_name="chatbot",
                        payload={
                            "tool_call_id": tool_call_id,
                            "tool_name": tool_name,
                            "args": self._json_safe(tool_args),
                        },
                    )

            elif isinstance(message, ToolMessage):
                tool_call_id = str(getattr(message, "tool_call_id", "") or "")
                tool_name = str(
                    getattr(message, "name", "") or tool_call_names.get(tool_call_id, "")
                )
                tool_content = self._extract_text(getattr(message, "content", ""))

                if not tool_call_id or tool_call_id in seen_tool_result_ids:
                    continue

                seen_tool_result_ids.add(tool_call_id)
                new_tool_result_ids.append(tool_call_id)

                await self.message_repo.create(
                    thread_id=thread_id,
                    user_id=user_id,
                    role="tool",
                    turn_id=turn_id,
                    kind="tool_result",
                    tool_name=tool_name,
                    tool_call_id=tool_call_id,
                    content_text=tool_content,
                    content_json={
                        "name": tool_name,
                    },
                )

                await self.event_repo.create(
                    thread_id=thread_id,
                    turn_id=turn_id,
                    event_type="tool_call_completed",
                    node_name="tools",
                    payload={
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_name,
                        "result_length": len(tool_content),
                    },
                )

        return new_tool_call_ids, new_tool_result_ids

    async def send_message(
        self,
        *,
        thread_id: uuid.UUID,
        user_id: uuid.UUID,
        message_text: str,
        idempotency_key: str,
    ) -> dict:
        await self.lock_repo.lock_thread_for_transaction(thread_id=thread_id)

        thread = await self.thread_repo.get_by_id(
            thread_id=thread_id,
            user_id=user_id,
        )
        if thread is None:
            raise ThreadNotFoundError("Thread not found")

        request_hash = self._make_request_hash(
            thread_id=thread_id,
            user_id=user_id,
            message_text=message_text,
        )

        existing_request = await self.request_repo.get_by_key(
            user_id=user_id,
            thread_id=thread_id,
            idempotency_key=idempotency_key,
        )

        if existing_request is not None:
            if existing_request.request_hash != request_hash:
                raise IdempotencyConflictError(
                    "Idempotency-Key already used for a different request"
                )

            if existing_request.status == "succeeded" and existing_request.response_json:
                return existing_request.response_json

            if existing_request.status == "started":
                raise RequestAlreadyProcessingError(
                    "Request is already processing or was interrupted"
                )

            if existing_request.status == "failed":
                raise RequestPreviouslyFailedError(
                    "Request previously failed. Please retry with a new Idempotency-Key"
                )

        turn_id = uuid.uuid4()

        request_record = await self.request_repo.create_started(
            user_id=user_id,
            thread_id=thread_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            turn_id=turn_id,
        )

        try:
            user_message = await self.message_repo.create(
                thread_id=thread_id,
                user_id=user_id,
                role="user",
                turn_id=turn_id,
                kind="message",
                content_text=message_text,
                content_json={
                    "idempotency_key": idempotency_key,
                },
            )

            await self.thread_repo.touch_last_message(thread_id=thread_id)

            result = await self.graph.ainvoke(
                {
                    "messages": [HumanMessage(content=message_text)]
                },
                config={
                    "configurable": {
                        "thread_id": str(thread_id),
                        "user_id": str(user_id),
                    }
                },
            )

            assistant_text = ""
            if result.get("messages"):
                last_message = result["messages"][-1]
                assistant_text = self._extract_text(
                    getattr(last_message, "content", "")
                )

            assistant_message = await self.message_repo.create(
                thread_id=thread_id,
                user_id=user_id,
                role="assistant",
                turn_id=turn_id,
                kind="message",
                content_text=assistant_text,
                content_json={
                    "provider": settings.llm_provider,
                    "model": settings.llm_model,
                    "idempotency_key": idempotency_key,
                },
                model_name=settings.llm_model,
            )

            await self.thread_repo.touch_last_message(thread_id=thread_id)

            response_json = {
                "thread_id": str(thread_id),
                "turn_id": str(turn_id),
                "user_message": user_message.content_text,
                "assistant_message": assistant_message.content_text,
            }

            await self.request_repo.mark_succeeded(
                request_id=request_record.id,
                response_json=response_json,
            )

            await self.db.commit()
            await self.db.refresh(user_message)
            await self.db.refresh(assistant_message)

            return response_json

        except Exception as exc:
            error_text = str(exc)

            await self.event_repo.create(
                thread_id=thread_id,
                turn_id=turn_id,
                event_type="chat_error",
                node_name="chat_service",
                payload={
                    "error": error_text,
                    "idempotency_key": idempotency_key,
                    "provider": settings.llm_provider,
                    "model": settings.llm_model,
                },
            )

            await self.request_repo.mark_failed(
                request_id=request_record.id,
                error_text=error_text,
            )

            await self.db.commit()

            raise ChatProcessingError("Chat processing failed") from exc
    
    async def stream_message(
        self,
        *,
        thread_id: uuid.UUID,
        user_id: uuid.UUID,
        message_text: str,
        idempotency_key: str,
    ) -> AsyncGenerator[str, None]:
        await self.lock_repo.lock_thread_for_transaction(thread_id=thread_id)

        thread = await self.thread_repo.get_by_id(
            thread_id=thread_id,
            user_id=user_id,
        )

        if thread is None:
            yield sse_event(
                event="error",
                data={
                    "code": "thread_not_found",
                    "message": "Thread not found",
                },
            )
            return

        request_hash = self._make_request_hash(
            thread_id=thread_id,
            user_id=user_id,
            message_text=message_text,
        )

        existing_request = await self.request_repo.get_by_key(
            user_id=user_id,
            thread_id=thread_id,
            idempotency_key=idempotency_key,
        )

        if existing_request is not None:
            if existing_request.request_hash != request_hash:
                yield sse_event(
                    event="error",
                    data={
                        "code": "idempotency_conflict",
                        "message": "Idempotency-Key already used for a different request",
                    },
                )
                return

            if existing_request.status == "succeeded" and existing_request.response_json:
                cached = existing_request.response_json

                yield sse_event(
                    event="start",
                    data={
                        "thread_id": cached.get("thread_id"),
                        "turn_id": cached.get("turn_id"),
                        "cached": True,
                    },
                )

                assistant_message = cached.get("assistant_message") or ""
                if assistant_message:
                    yield sse_event(
                        event="token",
                        data={
                            "text": assistant_message,
                            "cached": True,
                        },
                    )

                yield sse_event(
                    event="done",
                    data={
                        "thread_id": cached.get("thread_id"),
                        "turn_id": cached.get("turn_id"),
                        "cached": True,
                    },
                )
                return

            if existing_request.status == "started":
                yield sse_event(
                    event="error",
                    data={
                        "code": "request_already_processing",
                        "message": "Request is already processing or was interrupted",
                    },
                )
                return

            if existing_request.status == "failed":
                yield sse_event(
                    event="error",
                    data={
                        "code": "request_previously_failed",
                        "message": "Request previously failed. Please retry with a new Idempotency-Key",
                    },
                )
                return

        turn_id = uuid.uuid4()

        request_record = await self.request_repo.create_started(
            user_id=user_id,
            thread_id=thread_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            turn_id=turn_id,
        )

        assistant_chunks: list[str] = []
        latest_assistant_text = ""

        seen_tool_call_ids: set[str] = set()
        seen_tool_result_ids: set[str] = set()
        tool_call_names: dict[str, str] = {}

        try:
            await self.event_repo.create(
                thread_id=thread_id,
                turn_id=turn_id,
                event_type="chat_stream_started",
                node_name="chat_service",
                payload={
                    "message_length": len(message_text),
                    "provider": settings.llm_provider,
                    "model": settings.llm_model,
                    "idempotency_key": idempotency_key,
                },
            )

            user_message = await self.message_repo.create(
                thread_id=thread_id,
                user_id=user_id,
                role="user",
                turn_id=turn_id,
                kind="message",
                content_text=message_text,
                content_json={
                    "idempotency_key": idempotency_key,
                    "streamed": True,
                },
            )

            await self.thread_repo.touch_last_message(thread_id=thread_id)

            yield sse_event(
                event="start",
                data={
                    "thread_id": str(thread_id),
                    "turn_id": str(turn_id),
                },
            )

            async for part in self.graph.astream(
                {
                    "messages": [HumanMessage(content=message_text)]
                },
                config={
                    "configurable": {
                        "thread_id": str(thread_id),
                    }
                },
                context=GraphContext(user_id=str(user_id)),
                stream_mode=["messages", "updates"],
                version="v2",
            ):
                part_type = part.get("type")
                data = part.get("data")

                if part_type == "messages":
                    message_chunk, metadata = data
                    text = self._extract_text(
                        getattr(message_chunk, "content", "")
                    )

                    if not text:
                        continue

                    assistant_chunks.append(text)

                    yield sse_event(
                        event="token",
                        data={
                            "text": text,
                        },
                    )

                elif part_type == "updates":
                    update_messages = self._extract_messages_from_update(data)

                    for item in update_messages:
                        if isinstance(item, AIMessage):
                            tool_calls = getattr(item, "tool_calls", None) or []
                            if not tool_calls:
                                maybe_text = self._extract_text(
                                    getattr(item, "content", "")
                                )
                                if maybe_text:
                                    latest_assistant_text = maybe_text

                    new_tool_call_ids, new_tool_result_ids = await self._persist_tool_activity(
                        thread_id=thread_id,
                        user_id=user_id,
                        turn_id=turn_id,
                        messages=update_messages,
                        seen_tool_call_ids=seen_tool_call_ids,
                        seen_tool_result_ids=seen_tool_result_ids,
                        tool_call_names=tool_call_names,
                    )

                    await self.event_repo.create(
                        thread_id=thread_id,
                        turn_id=turn_id,
                        event_type="graph_update",
                        node_name=None,
                        payload={
                            "update": self._json_safe(data),
                        },
                    )

                    if new_tool_call_ids or new_tool_result_ids:
                        yield sse_event(
                            event="tool_update",
                            data={
                                "tool_calls_seen": new_tool_call_ids,
                                "tool_results_seen": new_tool_result_ids,
                            },
                        )

            assistant_text = "".join(assistant_chunks).strip()

            if not assistant_text:
                assistant_text = latest_assistant_text.strip()

            assistant_message = await self.message_repo.create(
                thread_id=thread_id,
                user_id=user_id,
                role="assistant",
                turn_id=turn_id,
                kind="message",
                content_text=assistant_text,
                content_json={
                    "provider": settings.llm_provider,
                    "model": settings.llm_model,
                    "idempotency_key": idempotency_key,
                    "streamed": True,
                },
                model_name=settings.llm_model,
            )

            await self.thread_repo.touch_last_message(thread_id=thread_id)

            response_json = {
                "thread_id": str(thread_id),
                "turn_id": str(turn_id),
                "user_message": user_message.content_text,
                "assistant_message": assistant_message.content_text,
            }

            await self.request_repo.mark_succeeded(
                request_id=request_record.id,
                response_json=response_json,
            )

            await self.event_repo.create(
                thread_id=thread_id,
                turn_id=turn_id,
                event_type="chat_stream_completed",
                node_name="chat_service",
                payload={
                    "assistant_message_id": str(assistant_message.id),
                    "assistant_text_length": len(assistant_text),
                    "tool_call_count": len(seen_tool_call_ids),
                    "tool_result_count": len(seen_tool_result_ids),
                },
            )

            await self.db.commit()
            await self.db.refresh(assistant_message)

            yield sse_event(
                event="done",
                data={
                    "thread_id": str(thread_id),
                    "turn_id": str(turn_id),
                    "assistant_message_id": str(assistant_message.id),
                },
            )

        except Exception as exc:
            error_text = str(exc)

            await self.event_repo.create(
                thread_id=thread_id,
                turn_id=turn_id,
                event_type="chat_stream_error",
                node_name="chat_service",
                payload={
                    "error": error_text,
                    "idempotency_key": idempotency_key,
                    "provider": settings.llm_provider,
                    "model": settings.llm_model,
                },
            )

            await self.request_repo.mark_failed(
                request_id=request_record.id,
                error_text=error_text,
            )

            await self.db.commit()

            yield sse_event(
                event="error",
                data={
                    "code": "chat_stream_failed",
                    "message": "Chat stream failed",
                    "detail": error_text,
                },
            )
