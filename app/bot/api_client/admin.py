"""Методы API-клиента Telegram-бота для admin-panel."""

from app.bot.api_client.base import BotApiClientBase
from app.bot.api_client.schemas.admin import BotAdminAccess, BotAdminStatus


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
