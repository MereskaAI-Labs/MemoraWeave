from langchain_core.messages import AIMessage


class FakeSuccessGraph:
    async def ainvoke(self, payload, config=None):
        return {
            "messages": [
                AIMessage(content="Ini jawaban fake assistant.")
            ]
        }


class FakeFailGraph:
    async def ainvoke(self, payload, config=None):
        raise RuntimeError("Fake graph failure")