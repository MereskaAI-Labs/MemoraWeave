from langchain.chat_models import init_chat_model

from app.core.config import settings


def build_chat_model():
    """
    Initializes and builds a LangChain chat model instance based on application settings.

    This function utilizes LangChain's `init_chat_model` factory to dynamically
    instantiate a chat model. The configuration parameters such as the provider,
    model name, temperature, and max tokens are injected directly from the
    global `settings` object.

    Returns:
        BaseChatModel: A configured LangChain chat model instance ready for use.
    """

    api_key = settings.google_api_key or settings.gemini_api_key

    if not api_key:
        raise RuntimeError(
            "API key Gemini belum terbaca. Isi GOOGLE_API_KEY atau GEMINI_API_KEY di .env"
        )

    return init_chat_model(
        settings.llm_model,
        model_provider=settings.llm_provider,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        api_key=api_key,
        vertexai=False,
    )
