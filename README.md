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