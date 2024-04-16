from aiogram.filters import BaseFilter
from aiogram.types import Message

from config_reader import config


class MainAdminFilter(BaseFilter):
    """
    Проверяет что пользователь является главным админом
    """
    def __init__(self):
        self.main_admin_id = int(config.MAIN_ADMIN_ID.get_secret_value())


    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == self.main_admin_id
        