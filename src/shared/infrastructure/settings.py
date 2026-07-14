from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseSettings):
    openai_api_key: str
    openai_model: str
    openai_timeout_seconds: int
    openai_base_url: str | None = None
    openai_organization: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("openai_timeout_seconds")
    @classmethod
    def _validate_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("openai_timeout_seconds must be positive")
        return value

    @field_validator("openai_base_url", "openai_organization", mode="before")
    @classmethod
    def _empty_string_as_none(cls, value: Any) -> Any:
        if value == "":
            return None
        return value


class DatabaseSettings(BaseSettings):
    database_async_url: str = (
        "postgresql+asyncpg://opositaria:opositaria_dev@localhost:5433/opositaria"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


class RabbitMQSettings(BaseSettings):
    rabbitmq_url: str = "amqp://opositaria:opositaria_dev@localhost:5673/"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


class DocumentStorageSettings(BaseSettings):
    document_storage_path: str = "./data/documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )
