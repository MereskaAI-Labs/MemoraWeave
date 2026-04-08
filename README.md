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