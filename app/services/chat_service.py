import hashlib
import uuid
from typing import Any

from langchain_core.messages import HumanMessage

from app.core.config import settings
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