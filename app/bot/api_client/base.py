"""Базовый HTTP-клиент Telegram-бота."""

from typing import TypeVar

import httpx

from app.core.config import config

_BotApiClientBaseT = TypeVar("_BotApiClientBaseT", bound="BotApiClientBase")


class BotApiClientBase:
    """Базовая часть клиента backend API для Telegram-бота."""

    def __init__(
        self,
        base_url: str | None = None,
        internal_api_token: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Создает клиент backend API для Telegram-бота.

        Args:
            base_url: базовый URL API. По умолчанию берется из `BOT_API_BASE_URL`.
            internal_api_token: service token для `/internal/*`.
            http_client: готовый `httpx.AsyncClient` для тестов или внешнего управления.
        """
        self.base_url = (base_url or config.BOT_API_BASE_URL).rstrip("/")
        self.internal_api_token = internal_api_token or config.INTERNAL_API_TOKEN.get_secret_value()
        self._client = http_client
        self._owns_client = http_client is None

    async def __aenter__(self: _BotApiClientBaseT) -> _BotApiClientBaseT:
        """Открывает HTTP-клиент, если он не был передан извне."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        """Закрывает HTTP-клиент, созданный внутри `BotApiClientBase`."""
        if self._owns_client and self._client is not None:
            await self._client.aclose()
        self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Возвращает открытый HTTP-клиент.

        Raises:
            RuntimeError: если клиент используется без `async with`.

        Returns:
            активный `httpx.AsyncClient` для internal API-запросов.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        return self._client
