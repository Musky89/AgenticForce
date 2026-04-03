from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AgenticForce"
    database_url: str = "sqlite+aiosqlite:///./agenticforce.db"

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Image Generation — Flux via fal.ai (supports LoRA)
    fal_key: str = ""
    flux_model: str = "fal-ai/flux/dev"
    flux_model_lora: str = "fal-ai/flux-lora"

    # Image Generation — Gemini Imagen (highest raw quality)
    gemini_api_key: str = ""
    imagen_model: str = "imagen-4.0-generate-001"

    # Default provider: "flux" (LoRA support) or "imagen" (raw quality)
    default_image_provider: str = "flux"

    # Security
    secret_key: str = "change-this-to-a-random-secret"
    access_token_expire_minutes: int = 60 * 24 * 7

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
