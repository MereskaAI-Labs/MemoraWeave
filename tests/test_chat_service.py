import uuid

import pytest
from sqlalchemy import text

from app.models.chat_thread import ChatThread
from app.repositories.message_repository import MessageRepository
from app.repositories.request_repository import RequestRepository
from app.services.chat_service import ChatService
from app.services.errors import ChatProcessingError
from tests.fakes import FakeFailGraph, FakeSuccessGraph


@pytest.mark.anyio
async def test_send_message_success(db_session):
    user_id = uuid.uuid4()

    thread = ChatThread(
        user_id=user_id,
        title="Test Thread",
        assistant_id="default",
        extra_metadata={},
    )
    db_session.add(thread)
    await db_session.flush()
    await db_session.refresh(thread)

    service = ChatService(db_session, FakeSuccessGraph())

    result = await service.send_message(
        thread_id=thread.id,
        user_id=user_id,
        message_text="Halo test",
        idempotency_key="test-key-001",
    )

    assert result["thread_id"] == str(thread.id)
    assert result["user_message"] == "Halo test"
    assert result["assistant_message"] == "Ini jawaban fake assistant."

    message_repo = MessageRepository(db_session)
    messages = await message_repo.list_by_thread(thread_id=thread.id)

    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


@pytest.mark.anyio
async def test_send_message_idempotency_returns_same_response(db_session):
    user_id = uuid.uuid4()

    thread = ChatThread(
        user_id=user_id,
        title="Idempotency Test",
        assistant_id="default",
        extra_metadata={},
    )
    db_session.add(thread)
    await db_session.flush()
    await db_session.refresh(thread)

    service = ChatService(db_session, FakeSuccessGraph())

    first = await service.send_message(
        thread_id=thread.id,
        user_id=user_id,
        message_text="Pesan yang sama",
        idempotency_key="same-key-001",
    )

    second = await service.send_message(
        thread_id=thread.id,
        user_id=user_id,
        message_text="Pesan yang sama",
        idempotency_key="same-key-001",
    )

    assert second == first

    message_repo = MessageRepository(db_session)
    messages = await message_repo.list_by_thread(thread_id=thread.id)

    assert len(messages) == 2


@pytest.mark.anyio
async def test_send_message_failure_marks_request_failed(db_session):
    user_id = uuid.uuid4()

    thread = ChatThread(
        user_id=user_id,
        title="Failure Test",
        assistant_id="default",
        extra_metadata={},
    )
    db_session.add(thread)
    await db_session.flush()
    await db_session.refresh(thread)

    service = ChatService(db_session, FakeFailGraph())

    with pytest.raises(ChatProcessingError):
        await service.send_message(
            thread_id=thread.id,
            user_id=user_id,
            message_text="Trigger failure",
            idempotency_key="fail-key-001",
        )

    request_repo = RequestRepository(db_session)
    request_record = await request_repo.get_by_key(
        user_id=user_id,
        thread_id=thread.id,
        idempotency_key="fail-key-001",
    )

    assert request_record is not None
    assert request_record.status == "failed"

    result = await db_session.execute(
        text(
            """
            select count(*)
            from app.chat_events
            where thread_id = :thread_id
              and event_type = 'chat_error'
            """
        ),
        {"thread_id": thread.id},
    )

    assert result.scalar_one() == 1