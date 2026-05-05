from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MemoraWeave API"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str

    # LangGraph short-term memory
    checkpointer_db_uri: str
    checkpointer_auto_setup: bool = False

    # LangGraph long-term memory
    store_db_uri: str
    store_auto_setup: bool = False

    # LLM configuration
    google_api_key: str | None = None
    gemini_api_key: str | None = None

    # LLM
    llm_provider: str = "google_genai"
    llm_model: str = "gemini-2.5-flash"
    llm_temperature: float = 0.0
    llm_max_tokens: int | None = 2048

    # Embeddings for semantic search

    # Free Model: gemini-embedding-2 / gemini-embedding-001; https://ai.google.dev/gemini-api/docs/embeddings
    # https://ai.google.dev/gemini-api/docs/pricing#gemini-embedding-2
    # https://ai.google.dev/gemini-api/docs/pricing#gemini-embedding-2
    #
    # gemini-embedding-2 Output dimension: Flexible, supports: 128 - 3072, Recommended: 768, 1536, 3072
    # gemini-embedding-001 Output dimension: Flexible, supports: 128 - 3072, Recommended: 768, 1536, 3072
    embedding_model: str = "gemini-embedding-2"
    embedding_dimensions: int = 768

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
