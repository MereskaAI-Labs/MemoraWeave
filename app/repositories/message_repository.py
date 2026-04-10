import uuid
from typing import Any

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        thread_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        turn_id: uuid.UUID,
        kind: str = "message",
        tool_name: str | None = None,
        tool_call_id: str | None = None,
        content_text: str | None = None,
        content_json: dict[str, Any] | None = None,
        model_name: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        latency_ms: int | None = None,
        checkpoint_id: str | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            thread_id=thread_id,
            user_id=user_id,
            role=role,
            kind=kind,
            turn_id=turn_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            content_text=content_text,
            content_json=content_json or {},
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            checkpoint_id=checkpoint_id,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def list_by_thread(
        self,
        *,
        thread_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.thread_id == thread_id)
            .order_by(asc(ChatMessage.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
