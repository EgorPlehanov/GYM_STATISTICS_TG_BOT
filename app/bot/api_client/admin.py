"""Методы API-клиента Telegram-бота для admin-panel."""

from dataclasses import dataclass

from app.bot.api_client.base import BotApiClientBase


@dataclass(frozen=True)
class BotAdminAccess:
    """Результат проверки доступа к Telegram admin-панели.

    Attributes:
        has_access: признак доступа к admin-панели.
        roles: коды ролей пользователя.
    """

    has_access: bool
    roles: list[str]


@dataclass(frozen=True)
class BotAdminStatus:
    """Минимальный статус backend API для Telegram admin-панели.

    Attributes:
        api_status: состояние backend API.
        app_env: текущее окружение приложения.
        has_access: признак доступа пользователя к admin-панели.
        roles: коды ролей пользователя.
    """

    api_status: str
    app_env: str
    has_access: bool
    roles: list[str]


class BotAdminApiClientMixin(BotApiClientBase):
    """Методы internal API для минимальной Telegram admin-panel."""

    async def get_admin_access(self, telegram_id: int) -> BotAdminAccess:
        """Проверяет доступ пользователя к Telegram admin-панели.

        Args:
            telegram_id: Telegram user id пользователя.

        Returns:
            результат проверки доступа и роли пользователя.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/admin/access",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={"telegram_id": telegram_id},
        )
        response.raise_for_status()
        return BotAdminAccess(**response.json())

    async def get_admin_status(self, telegram_id: int) -> BotAdminStatus:
        """Возвращает минимальный статус backend API для Telegram admin-панели.

        Args:
            telegram_id: Telegram user id пользователя.

        Returns:
            безопасный статус системы для администратора.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/admin/status",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={"telegram_id": telegram_id},
        )
        response.raise_for_status()
        return BotAdminStatus(**response.json())
