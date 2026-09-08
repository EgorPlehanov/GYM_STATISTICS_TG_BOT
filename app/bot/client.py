"""Клиент backend API для Telegram-бота."""

from dataclasses import dataclass

import httpx

from app.core.config import config


@dataclass(frozen=True)
class EnsureUserResult:
    """Результат регистрации пользователя через internal API.

    Attributes:
        created: признак того, что пользователь был создан в текущем запросе.
    """

    created: bool


@dataclass(frozen=True)
class BotExercise:
    """Упражнение, полученное ботом через backend API.

    Attributes:
        id: внутренний id упражнения из справочника.
        name: название упражнения для кнопок и inline-результатов.
        description: описание упражнения для inline-подсказки.
    """

    id: int
    name: str
    description: str | None


class BotApiClient:
    """HTTP-клиент, через который Telegram-бот обращается к backend API."""

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
        self.internal_api_token = (
            internal_api_token or config.INTERNAL_API_TOKEN.get_secret_value()
        )
        self._client = http_client
        self._owns_client = http_client is None

    async def __aenter__(self) -> "BotApiClient":
        """Открывает HTTP-клиент, если он не был передан извне."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        """Закрывает HTTP-клиент, созданный внутри `BotApiClient`."""
        if self._owns_client and self._client is not None:
            await self._client.aclose()
        self._client = None

    async def ensure_user(
        self,
        telegram_id: int,
        name: str,
        language_code: str | None,
    ) -> EnsureUserResult:
        """Создает пользователя через internal API, если его еще нет.

        Args:
            telegram_id: Telegram user id из update-а бота.
            name: отображаемое имя пользователя.
            language_code: языковой код пользователя из Telegram.

        Returns:
            `EnsureUserResult` с признаком создания пользователя.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.post(
            "/internal/bot/users/ensure",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "telegram_id": telegram_id,
                "name": name,
                "language_code": language_code,
            },
        )
        response.raise_for_status()
        return EnsureUserResult(**response.json())

    async def get_exercises(
        self,
        telegram_id: int,
        page_size: int = 50,
        page_num: int = 0,
        substring: str | None = None,
    ) -> list[BotExercise]:
        """Возвращает упражнения для выбора в Telegram-боте.

        Args:
            telegram_id: Telegram user id для пользовательской сортировки.
            page_size: размер страницы.
            page_num: номер страницы, начиная с 0.
            substring: строка поиска по справочнику упражнений.

        Returns:
            список упражнений в формате, удобном для handlers/keyboards бота.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        params: dict[str, int | str] = {
            "telegram_id": telegram_id,
            "page_size": page_size,
            "page_num": page_num,
        }
        if substring is not None:
            params["substring"] = substring

        response = await self._client.get(
            "/internal/bot/exercises",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params=params,
        )
        response.raise_for_status()
        return [BotExercise(**item) for item in response.json()]

    async def get_exercise(self, exercise_id: int) -> BotExercise:
        """Возвращает одно упражнение по id через internal API.

        Args:
            exercise_id: внутренний id упражнения из справочника.

        Returns:
            упражнение, найденное backend API.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.get(
            f"/internal/bot/exercises/{exercise_id}",
            headers={"X-Internal-Api-Key": self.internal_api_token},
        )
        response.raise_for_status()
        return BotExercise(**response.json())


