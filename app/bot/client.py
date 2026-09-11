"""Фасад API-клиента Telegram-бота."""

from app.bot.api_client.admin import BotAdminApiClientMixin
from app.bot.api_client.exercises import BotExercisesApiClientMixin
from app.bot.api_client.export import BotExportApiClientMixin
from app.bot.api_client.groups import BotGroupsApiClientMixin
from app.bot.api_client.schemas.admin import BotAdminAccess, BotAdminStatus
from app.bot.api_client.schemas.exercises import BotExercise
from app.bot.api_client.schemas.export import BotExportData
from app.bot.api_client.schemas.groups import (
    BotCurrentGroupRedirectToggleResult,
    BotRedirectGroup,
)
from app.bot.api_client.schemas.statistics import BotExerciseRating
from app.bot.api_client.schemas.trainings import (
    BotTrainingByDateResult,
    BotTrainingSaveResult,
    BotTrainingStartContext,
)
from app.bot.api_client.schemas.users import EnsureUserResult
from app.bot.api_client.statistics import BotStatisticsApiClientMixin
from app.bot.api_client.trainings import BotTrainingsApiClientMixin
from app.bot.api_client.users import BotUsersApiClientMixin

__all__ = [
    "BotAdminAccess",
    "BotAdminStatus",
    "BotApiClient",
    "BotCurrentGroupRedirectToggleResult",
    "BotExercise",
    "BotExerciseRating",
    "BotExportData",
    "BotRedirectGroup",
    "BotTrainingByDateResult",
    "BotTrainingSaveResult",
    "BotTrainingStartContext",
    "EnsureUserResult",
]


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
