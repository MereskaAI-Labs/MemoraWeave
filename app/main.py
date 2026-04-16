from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.api.v1.threads import router as threads_router
from app.core.config import settings
from app.db.session import engine
from app.graph.builder import build_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    # nanti disini kita pasang:
    # - database engine
    # - session factory

    # - langgraph checkpointer & store
    checkpoint_pool = AsyncConnectionPool(
        conninfo=settings.checkpointer_db_uri,
        max_size=25,
        open=False,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    )

    store_pool = AsyncConnectionPool(
        conninfo=settings.store_db_uri,
        max_size=25,
        open=False,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    )

    await checkpoint_pool.open()
    await store_pool.open()

    try:
        ckpt = AsyncPostgresSaver(checkpoint_pool)
        store = AsyncPostgresStore(store_pool)

        if settings.checkpointer_auto_setup:
            await ckpt.setup()

        if settings.store_auto_setup:
            await store.setup()

        ## Initialize Checkpoint & Store Pool in State of FastAPI
        app.state.checkpoint_pool = checkpoint_pool
        app.state.store_pool = store_pool
        ## Initialize Checkpointer & Store in State of FastAPI
        app.state.checkpointer = ckpt
        app.state.store = store
        ## Initialize Graph in State of FastAPI
        app.state.graph = build_graph(
            checkpointer=ckpt,
            store=store,
        )

        yield
    finally:
        await store_pool.close()
        await checkpoint_pool.close()
        await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(threads_router, prefix="/api/v1", tags=["threads"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
