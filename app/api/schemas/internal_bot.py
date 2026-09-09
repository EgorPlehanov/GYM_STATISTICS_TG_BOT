"""DTO-схемы internal API для Telegram-бота."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class InternalBotUserEnsureRequest(BaseModel):
    """Данные пользователя Telegram, которого нужно зарегистрировать для бота."""

    telegram_id: int
    name: str
    language_code: str | None = None


class InternalBotUserEnsureResponse(BaseModel):
    """Результат регистрации пользователя из Telegram-бота."""

    created: bool


class InternalBotExerciseResponse(BaseModel):
    """Упражнение из справочника для сценариев Telegram-бота."""

    id: int
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class InternalBotTrainingByDateResponse(BaseModel):
    """Данные тренировки за дату для сценариев Telegram-бота.

    Attributes:
        exists: признак того, что тренировка уже была в базе.
        training_data: структура тренировки в старом FSM-формате бота.
    """

    exists: bool
    training_data: dict[str, Any]
