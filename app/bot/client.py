"""Фасад API-клиента Telegram-бота."""

from app.bot.api_client.admin import BotAdminApiClientMixin
from app.bot.api_client.exercises import BotExercisesApiClientMixin
from app.bot.api_client.export import BotExportApiClientMixin
from app.bot.api_client.groups import BotGroupsApiClientMixin
from app.bot.api_client.statistics import BotStatisticsApiClientMixin
from app.bot.api_client.trainings import BotTrainingsApiClientMixin
from app.bot.api_client.users import BotUsersApiClientMixin

__all__ = ["BotApiClient"]


class BotApiClient(
    BotUsersApiClientMixin,
    BotAdminApiClientMixin,
    BotExercisesApiClientMixin,
    BotStatisticsApiClientMixin,
    BotExportApiClientMixin,
    BotGroupsApiClientMixin,
    BotTrainingsApiClientMixin,
):
    """HTTP-клиент, через который Telegram-бот обращается к backend API."""
