from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.api.v1.threads import router as threads_router
from app.core.config import settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # nanti disini kita pasang:
    # - database engine
    # - session factory
    # - langgraph checkpointer
    # - langgraph store
    yield

    # nanti disini cleanup resource
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(threads_router, prefix="/api/v1", tags=["threads"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
