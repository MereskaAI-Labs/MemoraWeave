from contextlib import asynccontextmanager
from logging import debug

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # nanti disini kita pasang:
    # - database engine
    # - session factory
    # - langgraph checkpointer
    # - langgraph store
    yield

    # nanti disini cleanup resource


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
