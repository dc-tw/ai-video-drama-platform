from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    comfyui_base_url: str = "http://localhost:8188"
    comfyui_checkpoint: str = "model.safetensors"
    comfyui_workflow_path: str = "comfyui/workflows/text_to_image_api.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
