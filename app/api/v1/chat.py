from fastapi import Header, APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.errors import (
    ChatProcessingError,
    IdempotencyConflictError,
    RequestAlreadyProcessingError,
    RequestPreviouslyFailedError,
    ThreadNotFoundError,
)

router = APIRouter()


def get_chat_service(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ChatService:
    return ChatService(
        db=db,
        graph=request.app.state.graph,
    )


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_chat(
    payload: ChatRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    service: ChatService = Depends(get_chat_service),
):
    try:
        result = await service.send_message(
            thread_id=payload.thread_id,
            user_id=payload.user_id,
            message_text=payload.message,
            idempotency_key=idempotency_key,
        )

        return ChatResponse(**result)

    except ThreadNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    except RequestAlreadyProcessingError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    except RequestPreviouslyFailedError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    except ChatProcessingError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/chat/stream")
async def stream_chat(
    payload: ChatRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    service: ChatService = Depends(get_chat_service),
):
    return StreamingResponse(
        service.stream_message(
            thread_id=payload.thread_id,
            user_id=payload.user_id,
            message_text=payload.message,
            idempotency_key=idempotency_key
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
