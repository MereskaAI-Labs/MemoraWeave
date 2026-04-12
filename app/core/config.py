from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MemoraWeave API"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str
    checkpointer_db_uri: str
    checkpointer_auto_setup: bool = False

    google_api_key: str | None = None
    gemini_api_key: str | None = None

    llm_provider: str = "google_genai"
    llm_model: str = "gemini-2.5-flash"
    llm_temperature: float = 0.0
    llm_max_tokens: int | None = 2048

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
