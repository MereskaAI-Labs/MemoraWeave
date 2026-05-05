from typing import Any

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from app.graph.context import GraphContext
from app.graph.state import ChatState
from app.llm.factory import build_chat_model
from app.memory.profile_memory import (
    extract_profile_updates,
    render_profile_for_prompt,
)
from app.memory.semantic_memory import (
    extract_memory_candidates,
    get_user_memories_namespace,
    render_semantic_memories_for_prompt,
    stable_memory_key,
)

llm = build_chat_model()

USER_PROFILE_NAMESPACE = ("users",)

def _message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return str(content or "")


async def chatbot_node(
    state: ChatState,
    runtime: Runtime[GraphContext],
) -> ChatState:
    if runtime.store is None:
        raise RuntimeError("LangGraph store is not configured")

    user_id = runtime.context.user_id
    memories_namespace  = get_user_memories_namespace(user_id=user_id)

    # 1) Read compact profile doc (7A)
    profile_item = await runtime.store.aget(USER_PROFILE_NAMESPACE, user_id)
    current_profile = profile_item.value if profile_item else {}

    # 2) Read current user message
    last_message = state["messages"][-1]
    last_text = getattr(last_message, "content", "") or ""
    if not isinstance(last_text, str):
        last_text = str(last_text)

    # 3) Semantic recall from memory collection (7B)
    memory_hits = await runtime.store.asearch(
        memories_namespace,
        query=last_text,
        limit=3,
    )
    semantic_memories_text = render_semantic_memories_for_prompt(memory_hits)

    # 4) Prepare profile prompt
    updated_profile = extract_profile_updates(last_text, current_profile)
    profile_text = render_profile_for_prompt(updated_profile)

    prompt_sections: list[str] = ["You are a helpful assistant."]

    if profile_text:
        prompt_sections.append(
            "Use the following user profile information if relevant:\n"
            f"{profile_text}"
        )
    
    if semantic_memories_text:
        prompt_sections.append(
            "Use the following recalled long-term memories if relevant:\n"
            f"{semantic_memories_text}"
        )

    system_text = "\n\n".join(prompt_sections)

    # 5) Call model
    response = await llm.ainvoke(
        [
            SystemMessage(content=system_text),
            *state["messages"],
        ]
    )

    # 6) Persist updated compact profile doc
    if updated_profile != current_profile:
        await runtime.store.aput(
            USER_PROFILE_NAMESPACE,
            user_id,
            updated_profile,
            index=False,  # profile doc itself does not need vector indexing
        )
    
    # 7) Persist semantic memory items
    memory_candidates  = extract_memory_candidates(last_text)
    for memory in memory_candidates:
        memory_key = stable_memory_key(memory["text"])
        await runtime.store.aput(
            memories_namespace,
            memory_key,
            memory,
            index=["text"]
        )

    return {"messages": [response]}


def build_graph(
    *,
    checkpointer: Any | None = None,
    store: Any | None = None,
):
    graph_builder = StateGraph(
        state_schema=ChatState,
        context_schema=GraphContext,
    )

    graph_builder.add_node("chatbot", chatbot_node)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)

    return graph_builder.compile(
        checkpointer=checkpointer,
        store=store,
    )
