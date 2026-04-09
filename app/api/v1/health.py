from fastapi import APIRouter

from app.db.session import ping_database

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "memoraweave-api",
    }


@router.get("/health/db")
async def health_db_check():
    db_ok = await ping_database()

    return {
        "status": "ok" if db_ok else "error",
        "database": "connected" if db_ok else "disconnected",
    }
