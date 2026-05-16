from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-08-01-preview"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    azure_openai_chat_deployment: str = "gpt-4o"

    azure_search_endpoint: str = ""
    azure_search_key: str = ""
    azure_search_index: str = "investimentos"

    chunk_size: int = Field(default=800, ge=100, le=4000)
    chunk_overlap: int = Field(default=120, ge=0, le=1000)
    top_k: int = Field(default=4, ge=1, le=20)
    embedding_dim: int = Field(default=1536, ge=128, le=4096)


@lru_cache
def get_settings() -> Settings:
    return Settings()
