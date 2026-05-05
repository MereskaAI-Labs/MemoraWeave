from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore, PoolConfig
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.api.v1.threads import router as threads_router
from app.core.config import settings
from app.db.session import engine
from app.embeddings.factory import build_embeddings
from app.graph.builder import build_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    # nanti disini kita pasang:
    # - database engine
    # - session factory

    # - langgraph checkpointer pool
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

    await checkpoint_pool.open()

    try:
        # - langgraph checkpointer
        checkpointer = AsyncPostgresSaver(checkpoint_pool)

        # - embeddings untuk semantic search di LangGraph Store
        embeddings = build_embeddings()

        # - langgraph store
        # pakai from_conn_string agar store bisa memakai:
        #   - connection pooling
        #   - index config untuk semantic/vector search
        async with AsyncPostgresStore.from_conn_string(
            settings.store_db_uri,
            pool_config=PoolConfig(
                min_size=5,
                max_size=25,
            ),
            index={
                "embed": embeddings,
                "dims": settings.embedding_dimensions,
                "fields": ["text"],
            },
        ) as store:
            # - setup database table untuk checkpointer & store
            if settings.checkpointer_auto_setup:
                await checkpointer.setup()

            if settings.langgraph_store_auto_setup:
                await store.setup()

            # Initialize Checkpoint Pool in State of FastAPI
            app.state.checkpoint_pool = checkpoint_pool

            # Initialize Checkpointer & Store in State of FastAPI
            app.state.checkpointer = checkpointer
            app.state.store = store

            # Initialize Graph in State of FastAPI
            app.state.graph = build_graph(
                checkpointer=checkpointer,
                store=store,
            )

            yield

    finally:
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
