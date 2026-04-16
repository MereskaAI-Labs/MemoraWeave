from typing import Any

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from app.graph.context import GraphContext
from app.graph.state import ChatState
from app.llm.factory import build_chat_model
from app.memory.profile_memory import extract_profile_updates, render_profile_for_prompt

llm = build_chat_model()

USER_PROFILE_NAMESPACE = ("users",)


async def chatbot_node(
    state: ChatState,
    runtime: Runtime[GraphContext],
) -> ChatState:
    assert runtime.store is not None

    user_id = runtime.context.user_id

    profile_item = await runtime.store.aget(USER_PROFILE_NAMESPACE, user_id)
    current_profile = profile_item.value if profile_item else {}

    last_message = state["messages"][-1]
    last_text = getattr(last_message, "content", "") or ""
    if not isinstance(last_text, str):
        last_text = str(last_text)

    updated_profile = extract_profile_updates(last_text, current_profile)

    if updated_profile != current_profile:
        await runtime.store.aput(
            USER_PROFILE_NAMESPACE,
            user_id,
            updated_profile,
        )

    profile_text = render_profile_for_prompt(updated_profile)

    if profile_text:
        system_text = (
            "You are a helpful assistant.\n"
            "Use the following user profile information if relevant:\n"
            f"{profile_text}"
        )
    else:
        system_text = "You are a helpful assistant."

    response = await llm.ainvoke(
        [
            SystemMessage(content=system_text),
            *state["messages"],
        ]
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
