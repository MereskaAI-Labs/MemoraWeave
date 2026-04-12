from typing import Any

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from app.graph.state import ChatState
from app.llm.factory import build_chat_model


async def chatbot_node(state: ChatState) -> ChatState:
    llm = build_chat_model()

    response = await llm.ainvoke(state["messages"])

    content = response.content
    if isinstance(content, str):
        assistant_text = content
    else:
        assistant_text = str(content)

    return {"messages": [AIMessage(content=assistant_text)]}


def build_graph(*, checkpointer: Any | None = None):
    graph_builder = StateGraph(state_schema=ChatState)

    graph_builder.add_node("chatbot", chatbot_node)

    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)

    return graph_builder.compile(checkpointer=checkpointer)
