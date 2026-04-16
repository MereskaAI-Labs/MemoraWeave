import uuid
from typing import Any

from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.graph.context import GraphContext
from app.repositories.message_repository import MessageRepository
from app.repositories.thread_repository import ThreadRepository


class ChatService:
    def __init__(self, db, graph):
        self.db = db
        self.graph = graph
        self.thread_repo = ThreadRepository(db)
        self.message_repo = MessageRepository(db)

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
    ) -> dict:

        thread = await self.thread_repo.get_by_id(
            thread_id=thread_id,
            user_id=user_id,
        )

        if thread is None:
            raise ValueError("Thread not found")

        turn_id = uuid.uuid4()

        user_message = await self.message_repo.create(
            thread_id=thread_id,
            user_id=user_id,
            role="user",
            turn_id=turn_id,
            kind="message",
            content_text=message_text,
            content_json={},
        )

        await self.thread_repo.touch_last_message(thread_id=thread_id)

        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=message_text)]},
            config={
                "configurable": {
                    "thread_id": str(thread_id),
                },
            },
            context=GraphContext(user_id=str(user_id)),
        )

        assistant_text = ""
        if result.get("messages"):
            last_message = result["messages"][-1]
            assistant_text = self._extract_text(getattr(last_message, "content", ""))

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
            },
            model_name=settings.llm_model,
        )

        await self.thread_repo.touch_last_message(thread_id=thread_id)

        await self.db.commit()
        await self.db.refresh(user_message)
        await self.db.refresh(assistant_message)

        return {
            "thread_id": thread_id,
            "turn_id": turn_id,
            "user_message": user_message.content_text,
            "assistant_message": assistant_message.content_text,
        }
