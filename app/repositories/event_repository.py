import uuid
from typing import Any

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_event import ChatEvent


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        thread_id: uuid.UUID,
        turn_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any],
        node_name: str | None = None,
    ) -> ChatEvent:
        event = ChatEvent(
            thread_id=thread_id,
            turn_id=turn_id,
            event_type=event_type,
            node_name=node_name,
            payload=payload,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_by_thread_turn(
        self,
        *,
        thread_id: uuid.UUID,
        turn_id: uuid.UUID,
    ) -> list[ChatEvent]:
        stmt = (
            select(ChatEvent)
            .where(ChatEvent.thread_id == thread_id, ChatEvent.turn_id == turn_id)
            .order_by(asc(ChatEvent.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
