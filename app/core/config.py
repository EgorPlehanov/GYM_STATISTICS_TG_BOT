"""Конфигурация приложения.

Модуль является единой точкой чтения переменных окружения для backend API,
Telegram-бота, web frontend, worker-процесса и базы данных.
"""

from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из окружения и `.env`.

    Обязательные секреты намеренно не имеют значений по умолчанию, чтобы
    приложение не запускалось в неверно настроенном окружении.
    """

    APP_ENV: Literal["dev", "test", "prod"] = "dev"
    APP_NAME: str = "Gym Statistics"

    MAIN_ADMIN_ID: SecretStr

    TG_BOT_TOKEN: SecretStr
    TG_BOT_USERNAME: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_BASE_URL: str = "http://api:8000"
    BOT_API_BASE_URL: str = "http://api:8000"
    INTERNAL_API_TOKEN: SecretStr = SecretStr("dev-only-internal-token")

    WEB_APP_URL: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    SESSION_SECRET_KEY: SecretStr = SecretStr("dev-only-change-me")
    SESSION_COOKIE_NAME: str = "gym_statistics_session"
    SESSION_TTL_SECONDS: int = 60 * 60 * 24 * 30
    COOKIE_DOMAIN: str | None = None
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Преобразует CORS origins из строки `.env` в список.

        Вход: строка с адресами через запятую или уже готовый список строк.
        Выход: список origin-адресов без пробелов и пустых значений.
        """
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("COOKIE_DOMAIN", mode="before")
    @classmethod
    def parse_cookie_domain(cls, value: str | None) -> str | None:
        """Преобразует пустой `COOKIE_DOMAIN` из `.env` в `None`."""
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Запрещает запуск production с dev-секретом сессии."""
        if (
            self.APP_ENV == "prod"
            and self.SESSION_SECRET_KEY.get_secret_value() == "dev-only-change-me"
        ):
            raise ValueError("SESSION_SECRET_KEY должен быть задан для prod-окружения")
        if (
            self.APP_ENV == "prod"
            and self.INTERNAL_API_TOKEN.get_secret_value() == "dev-only-internal-token"
        ):
            raise ValueError("INTERNAL_API_TOKEN должен быть задан для prod-окружения")
        return self

    @property
    def DB_URL_SYNC(self) -> str:
        """Возвращает sync DSN для SQLAlchemy/psycopg."""
        return (
            "postgresql+psycopg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DB_URL_ASYNC(self) -> str:
        """Возвращает async DSN для SQLAlchemy/asyncpg."""
        return (
            "postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = Settings()

__all__ = ["Settings", "config"]
