# Changelog

All notable changes to the **MemoraWeave** project will be documented in this file.

**The Standard Structure (SemVer)**
- **Major (X.y.z)**: Incremented for incompatible API changes (breaking changes).
- **Minor (x.Y.z)**: Incremented for new functionality introduced in a backward-compatible manner.
- **Patch (x.y.Z)**: Incremented for backward-compatible bug fixes or minor patches.

--

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
