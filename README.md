# MemoraWeave

> An advanced chatbot backend by **MereskaAI**, built to support scalable, intelligent, and memory-aware conversational AI services.

## Overview

**MemoraWeave** is a backend foundation for building conversational AI systems that need more than simple request-response interactions. It is designed for chatbot and agent-based applications that require persistent context, thread-based memory, tool usage, and flexible LLM orchestration.

This repository is currently in its early stage and provides the base structure for a scalable AI backend that can evolve into a production-ready system.

## Why MemoraWeave?

Modern AI assistants need to do more than generate responses. They need to:

- remember previous interactions
- manage multi-turn conversations across threads or sessions
- integrate with external tools and workflows
- support multiple model providers
- scale reliably as a backend service

MemoraWeave is intended to solve those needs through a modular and extensible architecture.

## Core Goals

- Build a **memory-aware conversational backend**
- Support **thread-based conversation management**
- Enable **LLM orchestration** across different providers
- Provide a clean foundation for **tool-calling and agent workflows**
- Keep the system **extensible, scalable, and developer-friendly**

## Planned / Supported Capabilities

The project is intended to support capabilities such as:

- Thread-based memory management
- Persistent conversation state
- Multi-session chatbot flows
- API-first backend architecture
- LLM provider integrations
- Tool-calling workflows
- Agentic orchestration patterns
- PostgreSQL-backed data persistence

## Tech Stack Direction

Based on the current project direction, MemoraWeave is aligned with technologies such as:

- **Python**
- **FastAPI**
- **PostgreSQL**
- **LangChain**
- **LangGraph**
- **Gemini**
- **Ollama**

> Note: Some integrations may still be under development depending on the current implementation status.

## Project Structure

```text
.
├── .python-version
├── CHANGELOG.md
├── LICENSE
├── README.md
├── main.py
└── pyproject.toml
```

### File Overview

* **main.py** — main application entry point
* **pyproject.toml** — project metadata and dependency configuration
* **CHANGELOG.md** — project change history
* **LICENSE** — repository license
* **.python-version** — local Python version reference

## Getting Started

### Prerequisites

Make sure you have:

* Python installed
* `pip` available
* PostgreSQL installed and running
* Access to any required LLM provider credentials

### Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/MemoraWeave.git
cd MemoraWeave
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -e .
```

Or, if editable install is not needed:

```bash
pip install .
```

## Configuration

Before running the project, prepare your environment variables or application config for things like:

* database connection
* app environment
* model provider credentials
* memory/session configuration
* API host and port

A typical setup may include:

```env
APP_ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/memoraweave
LLM_PROVIDER=gemini
```

> Adjust the configuration keys based on the actual implementation in your codebase.

## Run the Application

For the current scaffold, you can start with:

```bash
python main.py
```

If the app is later exposed as a FastAPI/ASGI service, you may switch to a command like:

```bash
uvicorn main:app --reload
```

> Use the command that matches your actual application entrypoint.

## Use Cases

MemoraWeave is suitable for systems such as:

* AI customer support backends
* internal knowledge assistants
* memory-aware chat applications
* multi-session AI copilots
* agent-based automation services
* LLM backends with persistent conversational context

## Development Roadmap

Planned areas of development may include:

* [ ] Core API endpoints
* [ ] Persistent memory engine
* [ ] Session and thread management
* [ ] PostgreSQL integration
* [ ] LLM provider abstraction
* [ ] Tool-calling support
* [ ] Agent workflow orchestration
* [ ] Authentication and access control
* [ ] Logging and observability
* [ ] Testing and CI/CD pipeline

## Contributing

Contributions are welcome.

To contribute:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

Please make sure your changes are clear, tested, and aligned with the project direction.

## Changelog

Project changes and updates are tracked in [CHANGELOG.md](./CHANGELOG.md).

## License

This project is licensed under the **MIT License**.
See [LICENSE](./LICENSE) for details.

## Maintainer

Built and maintained by **MereskaAI**.

---

## Project Status

This repository is currently in an **early development phase**.
The current structure serves as a foundation for future implementation and expansion.

---

## Phase 1: Simple Application Setup

To start the FastAPI application for development with auto-reload enabled, run:

```bash
uvicorn app.main:app --reload
```

### Verifying the Installation

Once the server is running, you can verify that the API is responding correctly by visiting the health check endpoint:

* **Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

**Expected Response:**

```json
{
  "status": "ok",
  "service": "memoraweave-api"
}
```

---

## Phase 2: Application Database Schema

In this phase, we focus on setting up the database tables for the application's UI and chat history. This is separate from LangGraph's internal persistence and serves as the source of truth for the product history.

### Target Architecture

We implement three core tables:

1.  **`app.chat_threads`**: Stores the list of conversation threads (useful for sidebars).
2.  **`app.chat_messages`**: Stores the full chat transcript.
3.  **`app.chat_events`**: Logs granular execution events (tool calls, streaming chunks, errors).

### SQL Initialization

The schema is defined in `app/db/sql/001_init_app_chat.sql`.

#### Schema Highlights

*   **Thread-based**: All messages and events are linked to a unique `thread_id`.
*   **Logical Turns**: Messages are grouped by `turn_id` to handle complex interactions (user input -> multiple tools -> assistant response) as a single unit.
*   **Separation of Concerns**: Events are kept in a separate table to keep the UI's message history clean and efficient.

### Running the SQL

To initialize the schema in your local PostgreSQL instance, you can use the following command:

```bash
psql "postgresql://postgres:postgres@localhost:5432/memoraweave" -f app/db/sql/001_init_app_chat.sql
```

> [!NOTE]
> Ensure your PostgreSQL service is running and the database `memoraweave` (or your chosen name) exists before running the command.

### External / VPS PostgreSQL Setup

If you are using an external PostgreSQL instance (e.g., on a VPS), the setup follows the same principles but requires a correct connection URI:

1.  **Connection URI**:
    ```env
    POSTGRES_URI="postgres://user:password@HOST:5432/memoraweave_db?sslmode=disable"
    ```
2.  **Schema Separation**:
    In the `memoraweave_db`, we use three schemas for clean separation:
    *   **`app`**: Application-owned tables (threads, messages, events).
    *   **`langgraph_ckpt`**: Reserved for LangGraph internal checkpoints.
    *   **`langgraph_store`**: Reserved for LangGraph long-term memory.
3.  **Bootstrapping**:
    You can use the `Query Tool` in pgAdmin or run the SQL script via `psql` remotely to initialize the structures. This ensures the application layer and runtime layer stay cleanly separated from the start.

---

## Phase 3: SQLAlchemy Async Integration

In this phase, we connect the FastAPI backend to our PostgreSQL database using **SQLAlchemy** with the **asyncpg** driver. This choice ensures an async end-to-end flow, which is ideal for streaming chat responses and managing multiple concurrent requests.

### Key Components

*   **Async Engine**: Configured in `app/db/session.py` using `create_async_engine`.
*   **Session Management**: An `async_sessionmaker` provides isolated database sessions for each request.
*   **Lifespan Management**: The database engine is gracefully disposed of during application shutdown.
*   **Database Health Check**: A new endpoint `/api/v1/health/db` allows for connectivity verification.

### Configuration

Ensure your `.env` file contains the correct `DATABASE_URL` using the `postgresql+asyncpg` scheme:

```env
DATABASE_URL=postgresql+asyncpg://user:password@HOST:5432/memoraweave_db
```

### Verifying Connectivity

You can test the database connection by running the server and hitting the following endpoint:

*   **DB Health Check**: [http://127.0.0.1:8000/api/v1/health/db](http://127.0.0.1:8000/api/v1/health/db)

**Example Response:**

```json
{
  "status": "ok",
  "database": "connected"
}
```
