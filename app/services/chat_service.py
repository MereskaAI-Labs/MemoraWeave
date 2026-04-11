import uuid

from app.graph.builder import build_graph
from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.repositories.message_repository import MessageRepository
from app.repositories.thread_repository import ThreadRepository


class ChatService:
    def __init__(self, db):
        self.db = db
        self.thread_repo = ThreadRepository(db)
        self.message_repo = MessageRepository(db)
        self.graph = build_graph()

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
        )

        assistant_text = ""
        if result.get("messages"):
            last_message = result["messages"][-1]
            assistant_text = getattr(last_message, "content", "") or ""

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
