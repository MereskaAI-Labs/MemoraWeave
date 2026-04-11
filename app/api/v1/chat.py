from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)

    try:
        result = await service.send_message(
            thread_id=payload.thread_id,
            user_id=payload.user_id,
            message_text=payload.message,
        )

        return ChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
