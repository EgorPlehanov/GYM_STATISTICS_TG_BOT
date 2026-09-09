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


class InternalBotTrainingSaveRequest(BaseModel):
    """Данные для сохранения тренировки из Telegram-бота.

    Attributes:
        training_data: структура тренировки в старом FSM-формате бота после JSON.
    """

    training_data: dict[str, Any]


class InternalBotTrainingSaveResponse(BaseModel):
    """Результат сохранения тренировки из Telegram-бота.

    Attributes:
        training_id: id сохраненной тренировки.
        updated: признак обновления существующей тренировки.
        created: признак создания новой тренировки.
    """

    training_id: int
    updated: bool
    created: bool


class InternalBotTrainingResultMessageCreateRequest(BaseModel):
    """Данные для создания записи о сообщении результата тренировки.

    Attributes:
        group_id: Telegram chat id группы.
        training_id: id сохраненной тренировки.
        message_id: Telegram message id отправленного результата.
    """

    group_id: int
    training_id: int
    message_id: int


class InternalBotTrainingResultMessageUpdateRequest(BaseModel):
    """Данные для обновления Telegram message id результата тренировки.

    Attributes:
        group_id: Telegram chat id группы.
        training_id: id сохраненной тренировки.
        new_message_id: новый Telegram message id после повторной отправки.
    """

    group_id: int
    training_id: int
    new_message_id: int


class InternalBotTrainingResultMessageUpdateResponse(BaseModel):
    """Результат обновления записи о сообщении результата тренировки.

    Attributes:
        updated: признак того, что существующая запись была найдена и обновлена.
    """

    updated: bool


class InternalBotGroupBotBannedRequest(BaseModel):
    """Данные для обновления признака недоступности группы для бота.

    Attributes:
        is_bot_banned: признак того, что бот удален или заблокирован в группе.
    """

    is_bot_banned: bool
