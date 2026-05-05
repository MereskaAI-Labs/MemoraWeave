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
uvicorn app.main:app --reload
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

---

## Phase 4: ORM Models and Repositories

In this phase, we bridge our database schema to the application layer using SQLAlchemy ORM models and the Repository pattern. This established a robust foundation for thread and message management before moving into LangGraph integration.

### Core Architecture

*   **ORM Models**: Located in `app/models/`, mapping `chat_threads`, `chat_messages`, and `chat_events` using SQLAlchemy 2.0's `Mapped` syntax.
*   **Repository Pattern**: Encapsulated database logic in `app/repositories/` to keep API endpoints clean and maintainable.
*   **Pydantic Schemas**: Defined in `app/schemas/` for strict request validation.
*   **Thread API**: A new router in `app/api/v1/threads.py` provides CRUD operations for conversations.

### Test Workflow

You can test the implementation using the Swagger Docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs):

1.  **Create Thread**: `POST /api/v1/threads` with a `user_id` and initial `title`.
2.  **Add Message**: `POST /api/v1/threads/{thread_id}/messages` to simulate user or assistant inputs.
3.  **List history**: Use `GET` endpoints to retrieve threads by user or messages by thread.

This setup ensures that even as we introduce complex AI logic later, our product history remains a reliable source of truth.

---

## Phase 5: Service Layer & LangGraph Integration

In this phase, we move beyond CRUD operations into a functional chat flow. We introduce a service layer to orchestrate the backend logic and integrate a minimal **LangGraph** structure for AI responses.

### Key Components

*   **Service Layer (`app/services/chat_service.py`)**: Centralizes the chat logic—validating threads, persisting messages, and invoking the AI graph.
*   **LLM Factory (`app/llm/factory.py`)**: Uses LangChain's `init_chat_model` for provider-agnostic initialization (defaulting to Google Gemini).
*   **LangGraph Integration (`app/graph/`)**: Implements a `StateGraph` that processes message history and generates assistant replies.
*   **Chat API**: A new endpoint `POST /api/v1/chat` that accepts user input and returns the full conversational turn.

### Workflow Recap

1.  **Request**: Client sends `thread_id` and `message`.
2.  **Persistence**: Backend saves the user message to `app.chat_messages`.
3.  **Inference**: The `ChatService` invokes the graph, which calls the configured LLM.
4.  **Completion**: The assistant's reply is automatically saved back to the database.
5.  **Response**: Client receives the full turn (user + assistant) for UI update.

### Configuration

Ensure your `.env` contains:
- `LLM_PROVIDER="google_genai"`
- `LLM_MODEL="gemini-2.5-flash"`
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` (required for inference)

### Test Command

`POST /api/v1/chat`
```json
{
  "thread_id": "YOUR_THREAD_UUID",
  "user_id": "YOUR_USER_UUID",
  "message": "Hello, how can you help me today?"
}
```

---

## Phase 6: LangGraph Persistence (PostgreSQL Checkpointer)

In this phase, we implemented persistent **short-term memory** for the AI agent using LangGraph's PostgreSQL checkpointer. This allows the assistant to maintain context across multiple turns within the same `thread_id`.

### Key Enhancements

*   **Persistence Layer**: Integrated `langgraph-checkpoint-postgres` to store conversational states (checkpoints) in PostgreSQL.
*   **Robust Lifecycle Management**: Implemented `AsyncConnectionPool` from `psycopg_pool` to handle checkpointer connections reliably within the FastAPI lifespan.
*   **Multi-turn Orchestration**: Updated `ChatService` to invoke the compiled graph with a persistent checkpointer, enabling the agent to "remember" previous interactions in the same thread.
*   **Separated Configuration**: Added dedicated environment variables for the checkpointer URI to support different connection requirements (e.g., `psycopg` vs `asyncpg`).

### Configuration Updates

Ensure your `.env` includes the following for the checkpointer:

```env
CHECKPOINTER_DB_URI=postgresql://user:password@HOST:5432/memoraweave_db?sslmode=disable
CHECKPOINTER_AUTO_SETUP=true
```

> [!TIP]
> Use `CHECKPOINTER_AUTO_SETUP=true` on the first run to automatically create the necessary `langgraph_ckpt` tables. You can set it to `false` afterwards.

### Manual Verification Workflow

1.  **Create a Thread**: Use `POST /api/v1/threads` to get a new `thread_id`.
2.  **First Message**: Send a message like "My name is Alice" to `POST /api/v1/chat`.
3.  **Second Message**: Send a follow-up like "What is my name?" to the **same** `thread_id`.
4.  **Expectation**: The assistant should correctly identify you as "Alice", proving that the state was successfully persisted and retrieved.

This milestone ensures that MemoraWeave is no longer just a "stateless" wrapper but a truly context-aware conversational backend.

---

## Phase 7A: Long-Term Memory (PostgreSQL Store)

In this phase, we implemented **long-term memory** using LangGraph's PostgreSQL Store (`AsyncPostgresStore`). This allows the assistant to remember user-specific profile information across multiple conversation threads.

### Key Enhancements

*   **Long-Term Store Layer**: Integrated `langgraph.store.postgres.aio.AsyncPostgresStore` to persist cross-thread state.
*   **Context Passing**: Introduced `GraphContext` to pass `user_id` natively into the LangGraph node execution.
*   **Profile Memory Architecture**: Added a simplistic rule-based profile extractor to identify a user's name, likes, and bio from messages. The profile is saved in the store and retrieved as context for subsequent queries, regardless of the active thread.
*   **Dual Memory Concept**: The system now seamlessly utilizes two memory layers simultaneously: short-term conversation state (`thread_id` via checkpointer) and long-term user profile context (`user_id` via store).

### Configuration Updates

Ensure your `.env` includes the following for the LangGraph store:

```env
STORE_DB_URI=postgresql://user:password@HOST:5432/memoraweave_db?sslmode=disable
LANGGRAPH_STORE_AUTO_SETUP=true
```

### Manual Verification Workflow

1.  **Create First Thread**: Get a `thread_id` using `POST /api/v1/threads`.
2.  **Provide Profile Info**: Send a message like "Nama saya Budi. Saya suka kopi." (My name is Budi. I like coffee.) to `POST /api/v1/chat`. The user profile will be extracted and stored.
3.  **Create Second Thread**: Get a new `thread_id` for the *same* `user_id`.
4.  **Test Cross-Thread Context**: In the new thread, ask "Siapa nama saya dan apa yang saya suka?" (What is my name and what do I like?).
5.  **Expectation**: The assistant should recall your name and preferences, demonstrating the integration of the long-term memory store across completely different conversation threads.

---

## Phase 7B: Semantic Long-Term Memory (Vector Search)

Building upon the persistent profile store, we have now introduced **Semantic Memory** powered by vector embeddings and PostgreSQL's vector extension. This enables the assistant to dynamically search and recall past user memories based on the semantic meaning of the user's current input, scoped entirely by `user_id`.

### Key Enhancements

*   **Vector Embeddings**: Integrated an embedding factory (`app.embeddings`) utilizing models like Google's `gemini-embedding-2` to convert user memories into high-dimensional vector representations.
*   **Semantic Search via LangGraph Store**: Upgraded `AsyncPostgresStore` initialization to leverage `index` configurations. We now perform semantic vector similarity search (`asearch`) on memory namespaces.
*   **Dynamic Candidate Extraction**: Implemented a memory extractor (`app.memory.semantic_memory`) to automatically identify and isolate episodic or declarative memories from raw user inputs.
*   **Namespace Scoping**: All memories are securely namespaced per user (`("memories", str(user_id))`) ensuring strict data isolation across conversations and users.
*   **Tri-Layer Memory System**: MemoraWeave now leverages three distinct memory paradigms:
    1.  **Short-term Thread Memory**: Context within a specific conversation (`checkpointer`).
    2.  **Long-term Profile Document**: A compact, structured profile of the user (`store.aget`).
    3.  **Long-term Semantic Memory**: A vector-searchable database of distinct memories and events (`store.asearch`).

### Configuration Updates

To support vector embeddings, add the following to your `.env`:

```env
EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSIONS=768
```

Ensure your PostgreSQL database has the `pgvector` extension enabled (LangGraph handles the vector schema setup automatically when `LANGGRAPH_STORE_AUTO_SETUP=true`).

### Manual Verification Workflow

1.  **Create a Thread**: Get a `thread_id` using `POST /api/v1/threads`.
2.  **Save a Memory**: Send a message like "Tahun lalu saya pergi liburan ke Bali dan sangat menyukai pantainya." to `POST /api/v1/chat`. The system will extract this as a distinct memory candidate, embed it, and save it to the vector store.
3.  **Create a New Thread**: Get a new `thread_id` for the *same* `user_id`.
4.  **Recall the Memory Semantically**: In the new thread, ask "Apakah kamu ingat ke mana saya pergi liburan tahun lalu?".
5.  **Expectation**: The assistant will perform a vector search, retrieve the semantic memory about your trip to Bali, inject it into the prompt, and accurately answer your question despite it being a completely new conversation thread.
