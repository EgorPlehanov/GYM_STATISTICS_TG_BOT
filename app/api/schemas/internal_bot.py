"""DTO-схемы internal API для Telegram-бота."""

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
