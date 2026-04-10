import uuid
from typing import Any

# APIRouter: untuk membuat kumpulan endpoint
# Depends: untuk dependency injection, misalnya ambil koneksi DB
# HTTPException: untuk melempar error HTTP seperti 404
# Query: untuk mendefinisikan query parameter
# status: konstanta status code HTTP, misalnya 201 Created
from fastapi import APIRouter, Depends, HTTPException, Query, status

# AsyncSession adalah session database async dari SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession

# get_db adalah dependency yang akan memberi kita object session database
from app.db.session import get_db

# Model ORM yang merepresentasikan tabel database
from app.models.chat_message import ChatMessage
from app.models.chat_thread import ChatThread

# Repository dipakai agar logic query database tidak ditulis langsung di endpoint
from app.repositories.message_repository import MessageRepository
from app.repositories.thread_repository import ThreadRepository

# Schema request dari Pydantic untuk validasi body request
from app.schemas.thread import CreateMessageRequest, CreateThreadRequest

# Router untuk endpoint yang berhubungan dengan thread dan message
router = APIRouter()


def serialize_thread(thread: ChatThread) -> dict[str, Any]:
    """
    Mengubah object ORM ChatThread menjadi dict biasa
    agar aman dan mudah dikirim sebagai JSON response.
    """

    return {
        # UUID diubah ke string supaya bisa diserialisasi ke JSON
        "id": str(thread.id),
        "user_id": str(thread.user_id),
        # Field standar dari tabel thread
        "assistant_id": thread.assistant_id,
        "title": thread.title,
        "title_generated": thread.title_generated,
        "archived": thread.archived,
        # Datetime diubah ke format ISO string supaya JSON-compatible
        "created_at": thread.created_at.isoformat() if thread.created_at else None,
        "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
        "last_message_at": thread.last_message_at.isoformat()
        if thread.last_message_at
        else None,
        # Di model Python namanya extra_metadata, tapi di response kita tampilkan sebagai metadata
        "metadata": thread.extra_metadata or {},
    }


def serialize_message(message: ChatMessage) -> dict[str, Any]:
    """
    Mengubah object ORM ChatMessage menjadi dict biasa
    agar bisa dikembalikan sebagai JSON response.
    """

    return {
        # UUID diubah ke string
        "id": str(message.id),
        "thread_id": str(message.thread_id),
        "user_id": str(message.user_id),
        # Informasi dasar pesan
        "role": message.role,
        "kind": message.kind,
        "turn_id": str(message.turn_id),
        # Dipakai jika pesan berkaitan dengan tool call / tool result
        "tool_name": message.tool_name,
        "tool_call_id": message.tool_call_id,
        # Isi utama pesan
        "content_text": message.content_text,
        "content_json": message.content_json or {},
        # Metadata tambahan untuk observability / analytics
        "model_name": message.model_name,
        "input_tokens": message.input_tokens,
        "output_tokens": message.output_tokens,
        "latency_ms": message.latency_ms,
        "checkpoint_id": message.checkpoint_id,
        # Waktu pesan dibuat
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


@router.post("/threads", status_code=status.HTTP_201_CREATED)
async def create_thread(
    payload: CreateThreadRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint untuk membuat thread baru.

    Alur:
    1. Terima body request yang sudah divalidasi oleh Pydantic
    2. Buat repository thread
    3. Simpan thread baru ke database
    4. Commit transaksi
    5. Refresh object agar field dari DB seperti id/created_at ikut terisi
    6. Kembalikan hasil dalam bentuk JSON
    """

    # Buat repository dengan session DB aktif
    repo = ThreadRepository(db)

    # Simpan thread baru ke database
    thread = await repo.create(
        user_id=payload.user_id,
        assistant_id=payload.assistant_id,
        title=payload.title,
        metadata=payload.metadata,
    )

    # Simpan perubahan secara permanen ke database
    await db.commit()

    # Refresh object dari database supaya server_default seperti id/created_at ikut terambil
    await db.refresh(thread)

    # Ubah object ORM menjadi dict JSON-friendly
    return serialize_thread(thread)


@router.get("/threads")
async def list_threads(
    user_id: uuid.UUID = Query(...),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint untuk mengambil daftar thread milik user tertentu.

    Query parameter:
    - user_id: wajib, untuk menentukan thread milik siapa
    - limit: jumlah maksimum data yang diambil
    - offset: untuk pagination
    """

    repo = ThreadRepository(db)

    # Ambil daftar thread berdasarkan user_id
    threads = await repo.list_by_user(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

    # Ubah semua object ORM menjadi list dict
    return [serialize_thread(item) for item in threads]


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: uuid.UUID,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint untuk mengambil detail satu thread.

    Keamanan dasar di sini:
    thread dicari berdasarkan thread_id + user_id,
    jadi user hanya bisa mengambil thread miliknya sendiri.
    """

    repo = ThreadRepository(db)

    # Cari thread berdasarkan id dan pemiliknya
    thread = await repo.get_by_id(thread_id=thread_id, user_id=user_id)

    # Kalau tidak ditemukan, kirim error 404
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    return serialize_thread(thread)


@router.post("/threads/{thread_id}/messages", status_code=status.HTTP_201_CREATED)
async def create_message(
    thread_id: uuid.UUID,
    payload: CreateMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint untuk menambahkan message ke thread tertentu.

    Alur:
    1. Pastikan thread ada dan milik user yang benar
    2. Simpan message baru
    3. Update last_message_at pada thread
    4. Commit transaksi
    5. Refresh object message
    6. Return hasil
    """

    # Repository thread dipakai untuk cek thread dan update last_message_at
    thread_repo = ThreadRepository(db)

    # Repository message dipakai untuk insert pesan baru
    message_repo = MessageRepository(db)

    # Pastikan thread benar-benar ada dan milik user yang mengirim request
    thread = await thread_repo.get_by_id(
        thread_id=thread_id,
        user_id=payload.user_id,
    )

    # Kalau thread tidak ada, tidak boleh insert message
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Simpan message baru
    message = await message_repo.create(
        thread_id=thread_id,
        user_id=payload.user_id,
        role=payload.role,
        turn_id=payload.turn_id,
        kind=payload.kind,
        tool_name=payload.tool_name,
        tool_call_id=payload.tool_call_id,
        content_text=payload.content_text,
        content_json=payload.content_json,
        model_name=payload.model_name,
        input_tokens=payload.input_tokens,
        output_tokens=payload.output_tokens,
        latency_ms=payload.latency_ms,
        checkpoint_id=payload.checkpoint_id,
    )

    # Setelah ada pesan baru, update last_message_at thread
    # supaya urutan thread di sidebar bisa berdasarkan aktivitas terbaru
    await thread_repo.touch_last_message(thread_id=thread_id)

    # Simpan transaksi
    await db.commit()

    # Refresh message agar field dari DB ikut terisi penuh
    await db.refresh(message)

    return serialize_message(message)


@router.get("/threads/{thread_id}/messages")
async def list_messages(
    thread_id: uuid.UUID,
    user_id: uuid.UUID = Query(...),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint untuk mengambil daftar message dari satu thread.

    Alur:
    1. Pastikan thread ada dan milik user
    2. Ambil daftar message berdasarkan thread_id
    3. Return sebagai JSON
    """

    thread_repo = ThreadRepository(db)
    message_repo = MessageRepository(db)

    # Cek dulu thread valid dan milik user yang benar
    thread = await thread_repo.get_by_id(
        thread_id=thread_id,
        user_id=user_id,
    )

    # Kalau thread tidak ditemukan, return 404
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Ambil daftar message milik thread tersebut
    messages = await message_repo.list_by_thread(
        thread_id=thread_id,
        limit=limit,
        offset=offset,
    )

    # Serialize semua message ke bentuk dict
    return [serialize_message(item) for item in messages]
