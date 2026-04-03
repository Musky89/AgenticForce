from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AgenticForce"
    database_url: str = "sqlite+aiosqlite:///./agenticforce.db"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    secret_key: str = "change-this-to-a-random-secret"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
