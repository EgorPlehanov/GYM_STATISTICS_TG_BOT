"""Методы API-клиента Telegram-бота для пользователей."""

from dataclasses import dataclass

from app.bot.api_client.base import BotApiClientBase


@dataclass(frozen=True)
class EnsureUserResult:
    """Результат регистрации пользователя через internal API.

    Attributes:
        created: признак того, что пользователь был создан в текущем запросе.
    """

    created: bool


class BotUsersApiClientMixin(BotApiClientBase):
    """Методы internal API для пользовательских операций Telegram-бота."""

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
        client = self._get_client()

        response = await client.post(
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

    async def update_user_private_chat_banned(
        self,
        telegram_id: int,
        is_private_chat_banned: bool,
    ) -> None:
        """Обновляет признак блокировки бота пользователем в личном чате.

        Args:
            telegram_id: Telegram user id пользователя.
            is_private_chat_banned: признак того, что пользователь заблокировал бота.
        """
        client = self._get_client()

        response = await client.patch(
            f"/internal/bot/users/{telegram_id}/private-chat-banned",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={"is_private_chat_banned": is_private_chat_banned},
        )
        response.raise_for_status()

    async def recalculate_user_rating(self, telegram_id: int) -> None:
        """Запускает пересчет рейтингов пользователя через internal API.

        Args:
            telegram_id: Telegram user id пользователя.
        """
        client = self._get_client()

        response = await client.post(
            f"/internal/bot/users/{telegram_id}/rating/recalculate",
            headers={"X-Internal-Api-Key": self.internal_api_token},
        )
        response.raise_for_status()
