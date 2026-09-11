from aiogram.filters import BaseFilter
from aiogram.types import Message
from httpx import HTTPError

from app.bot.client import BotApiClient
from app.core.config import config


class MainAdminFilter(BaseFilter):
    """
    Проверяет доступ пользователя к минимальной Telegram admin-панели.
    """

    def __init__(self):
        self.main_admin_id = int(config.MAIN_ADMIN_ID.get_secret_value())

    async def __call__(self, message: Message) -> bool:
        try:
            async with BotApiClient() as api_client:
                access = await api_client.get_admin_access(message.from_user.id)
        except HTTPError:
            # Emergency fallback нужен, чтобы владелец мог открыть admin status
            # при ошибке сети, API или service-to-service token.
            return message.from_user.id == self.main_admin_id

        return access.has_access
