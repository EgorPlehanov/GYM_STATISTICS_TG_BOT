"""Методы API-клиента Telegram-бота для экспорта."""

from app.bot.api_client.base import BotApiClientBase
from app.bot.api_client.schemas.export import BotExportData, deserialize_export_data


class BotExportApiClientMixin(BotApiClientBase):
    """Методы internal API для экспорта данных Telegram-бота."""

    async def get_export_data(self, telegram_id: int) -> list[BotExportData]:
        """Возвращает данные для XLSX-экспорта через internal API.

        Args:
            telegram_id: Telegram user id пользователя.

        Returns:
            строки данных для формирования файла экспорта в Telegram-боте.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/export/data",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={"telegram_id": telegram_id},
        )
        response.raise_for_status()
        return [deserialize_export_data(item) for item in response.json()]
