from langchain_core.tools import tool


@tool
def get_project_stage() -> str:
    """
    Return the current backend development stage for the MemoraWeave project.

    Use this when the user asks about:
    - current backend implementation stage
    - progress
    - roadmap
    - what feature is being developed now
    """
    return (
        "Current stage: Tahap 9B. "
        "The backend already has FastAPI, PostgreSQL app tables, "
        "LangGraph checkpointer, LangGraph store, semantic memory, "
        "idempotency, thread locking, and is now adding streaming, "
        "tool calling, tool result persistence, and audit events."
    )