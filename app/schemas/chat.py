import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    thread_id: uuid.UUID
    user_id: uuid.UUID
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    thread_id: uuid.UUID
    turn_id: uuid.UUID
    user_message: str
    assistant_message: str
