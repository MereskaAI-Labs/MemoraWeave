from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
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
from app.tools.project_tools import get_project_stage

llm = build_chat_model()

tools = [
    get_project_stage,
]

llm_with_tools = llm.bind_tools(tools)

USER_PROFILE_NAMESPACE = ("users",)

def _message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text_value = item.get("text")
                if text_value:
                    parts.append(str(text_value))

        return "\n".join(part for part in parts if part)

    return str(content or "")

def _latest_human_text(messages: list[Any]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return _message_content_to_text(getattr(message, "content", ""))

    if not messages:
        return ""

    return _message_content_to_text(getattr(messages[-1], "content", ""))


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
    messages = state["messages"]
    last_message = messages[-1]
    latest_user_text = _latest_human_text(messages)

    should_write_memory = isinstance(last_message, HumanMessage)

    search_text = latest_user_text or _message_content_to_text(
        getattr(last_message, "content", "")
    )

    # 3) Semantic recall from memory collection (7B)
    memory_hits = []
    if search_text:
        memory_hits = await runtime.store.asearch(
            memories_namespace,
            query=search_text,
            limit=3,
        )
    semantic_memories_text = render_semantic_memories_for_prompt(memory_hits)

    # 4) Prepare profile prompt
    if should_write_memory:
        updated_profile = extract_profile_updates(
            latest_user_text,
            current_profile,
        )
    else:
        updated_profile = current_profile
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
    response = await llm_with_tools.ainvoke(
        [
            SystemMessage(content=system_text),
            *messages,
        ]
    )

    # 6) Persist updated compact profile doc
    if should_write_memory and updated_profile != current_profile:
        await runtime.store.aput(
            USER_PROFILE_NAMESPACE,
            user_id,
            updated_profile,
            index=False,  # profile doc itself does not need vector indexing
        )
    
    # 7) Persist semantic memory items
    if should_write_memory:
        memory_candidates = extract_memory_candidates(latest_user_text)
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
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "chatbot")

    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    graph_builder.add_edge("tools", "chatbot")

    return graph_builder.compile(
        checkpointer=checkpointer,
        store=store,
    )
