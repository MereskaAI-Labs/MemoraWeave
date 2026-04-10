import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class CreateThreadRequest(BaseModel):
    user_id: uuid.UUID
    assistant_id: str = "default"
    title: str = "New Chat"
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateMessageRequest(BaseModel):
    user_id: uuid.UUID
    role: Literal["user", "assistant", "tool", "system"]
    turn_id: uuid.UUID
    kind: str = "message"
    tool_name: str | None = None
    tool_call_id: str | None = None
    content_text: str | None = None
    content_json: dict[str, Any] = Field(default_factory=dict)
    model_name: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    checkpoint_id: str | None = None
