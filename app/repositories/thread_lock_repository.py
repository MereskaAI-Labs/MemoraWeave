from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class ThreadLockRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def lock_thread_for_transaction(
        self,
        *,
        thread_id: UUID,
    ) -> None:
        
        lock_key = f"chat_thread:{thread_id}"

        await self.session.execute(
            text(
                """
                select pg_advisory_xact_lock(
                    ('x' || substr(md5(:lock_key), 1, 8))::bit(32)::int,
                    ('x' || substr(md5(:lock_key), 9, 8))::bit(32)::int
                )
                """
            ),
            {"lock_key": lock_key},
        )