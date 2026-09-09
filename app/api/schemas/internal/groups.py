"""DTO-схемы internal API для Telegram-групп."""

from pydantic import BaseModel


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
