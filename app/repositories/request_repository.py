import uuid
from typing import Any

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_request import ChatRequest

class RequestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_key(
        self,
        *,
        user_id: uuid.UUID,
        thread_id: uuid.UUID,
        idempotency_key: str,
    ) -> ChatRequest | None :
        
        stmt = select(ChatRequest).where(
            ChatRequest.user_id == user_id,
            ChatRequest.thread_id == thread_id,
            ChatRequest.idempotency_key == idempotency_key
        )

        result = await self.session.execute(stmt)
        
        return result.scalar_one_or_none()
    
    async def create_started(
        self,
        *,
        user_id: uuid.UUID,
        thread_id: uuid.UUID,
        idempotency_key: str,
        request_hash: str,
        turn_id: uuid.UUID,
    ) -> ChatRequest:

        item = ChatRequest(
            user_id=user_id,
            thread_id=thread_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            turn_id=turn_id,
        )

        self.session.add(item)

        await self.session.flush()

        return item
    
    async def mark_succeeded(
        self,
        *,
        request_id: uuid.UUID,
        response_json: dict[str, Any],
    ) -> None:

        stmt = (
            update(ChatRequest)
            .where(ChatRequest.id == request_id)
            .values(
                status="succeded",
                response_json=response_json,
                updated_at=func.now()
            )
        )

        await self.session.execute(stmt)
    
    async def mark_failed(
        self,
        *,
        request_id: uuid.UUID,
        error_text: str,
    ) -> None:
        
        stmt = (
            update(ChatRequest)
            .where(ChatRequest.id == request_id)
            .values(
                status="failed",
                error_text=error_text,
                updated_at=func.now()
            )
        )

        await self.session.execute(stmt)
