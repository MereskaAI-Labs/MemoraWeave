import uuid

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_thread import ChatThread


class ThreadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        assistant_id: str = "default",
        title: str = "New Chat",
        metadata: dict | None = None,
    ) -> ChatThread:
        thread = ChatThread(
            user_id=user_id,
            assistant_id=assistant_id,
            title=title,
            extra_metadata=metadata or {},
        )
        self.session.add(thread)
        await self.session.flush()
        return thread

    async def get_by_id(
        self,
        *,
        thread_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> ChatThread | None:
        stmt = select(ChatThread).where(ChatThread.id == thread_id)

        if user_id is not None:
            stmt = stmt.where(ChatThread.user_id == user_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        *,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatThread]:
        stmt = (
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .order_by(desc(ChatThread.last_message_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def touch_last_message(
        self,
        *,
        thread_id: uuid.UUID,
    ) -> None:
        stmt = (
            update(ChatThread)
            .where(ChatThread.id == thread_id)
            .values(
                last_message_at=func.now(),
                updated_at=func.now(),
            )
        )
        await self.session.execute(stmt)
