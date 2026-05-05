# Changelog

All notable changes to the **MemoraWeave** project will be documented in this file.

**The Standard Structure (SemVer)**
- **Major (X.y.z)**: Incremented for incompatible API changes (breaking changes).
- **Minor (x.Y.z)**: Incremented for new functionality introduced in a backward-compatible manner.
- **Patch (x.y.Z)**: Incremented for backward-compatible bug fixes or minor patches.

--

## [0.1.10] - 2026-05-06
### Added
- Semantic Memory capabilities using LangGraph `AsyncPostgresStore` with vector indexing.
- New `app.memory.semantic_memory` module for extracting and managing semantic memories.
- Embeddings factory (`app.embeddings`) for vector generation.
- Configurable `EMBEDDING_MODEL` and `EMBEDDING_DIMENSIONS` settings.
- Integration of LangGraph store `index` configuration with PostgreSQL vector extensions.

### Changed
- Refactored `AsyncPostgresStore` initialization in `app/main.py` to use `from_conn_string` with `PoolConfig`.
- Pinned and upgraded dependency versions in `requirements.txt` (added `langchain-google-vertexai`).


## [0.1.9] - 2026-04-16
### Added
- Long-term memory profile using LangGraph `AsyncPostgresStore`.
- `GraphContext` definition to pass `user_id` context to the graph.
- Rule-based profile extraction (`name`, `likes`, `bio`) to test profile memory mechanics.
- `AsyncConnectionPool` utilization for the LangGraph store connection lifecycle.
- Dedicated `STORE_DB_URI` and `LANGGRAPH_STORE_AUTO_SETUP` environment variables.
- Phase 7A documentation in README.

## [0.1.8] - 2026-04-12
### Added
- PostgreSQL checkpointer integration for persistent thread-level memory.
- `AsyncConnectionPool` usage for the checkpointer to ensure robust connection management.
- Dedicated `CHECKPOINTER_DB_URI` and `CHECKPOINTER_AUTO_SETUP` environment variables.
- Phase 6 documentation in README.

### Fixed
- `OperationalError`: Fixed connection lifecycle issues where the checkpointer would attempt to use a closed connection by implementing a connection pool.

## [0.1.7] - 2026-04-12
### Added
- Service Layer (`ChatService`) for orchestrating conversational flows.
- Minimal LangGraph integration with a single chatbot node.
- Abstract LLM factory using `init_chat_model` (Gemini default).
- Chat API endpoint `POST /api/v1/chat`.
- Phase 5 recap in README.

## [0.1.6] - 2026-04-10
### Added
- ORM models for `ChatThread`, `ChatMessage`, and `ChatEvent`.
- Repository layer (`ThreadRepository`, `MessageRepository`, `EventRepository`) for database access.
- API endpoints for thread management and manual message creation.
- Phase 4 recap in README.

## [0.1.5] - 2026-04-09
### Added
- SQLAlchemy async integration with `asyncpg`.
- Database session management and engine lifespan handling.
- Database connectivity health check endpoint (`/api/v1/health/db`).
- Phase 3 documentation in README.

## [0.1.4] - 2026-04-09
### Added
- External / VPS PostgreSQL setup documentation in README.

## [0.1.3] - 2026-04-09
### Added
- Application-level database schema for chat history (`chat_threads`, `chat_messages`, `chat_events`).
- Phase 2 documentation in README.

## [0.1.2] - 2026-04-09
### Added
- Comprehensive `.gitignore` for Python and environment variables.
### Changed
- Refined README documentation for FastAPI service (Quick Start).

## [0.1.1] - 2026-04-08
### Added
- Project description to README.
- Initial release documentation.

## [0.1.0] - 2026-04-08
### Added
- Initial project release.
