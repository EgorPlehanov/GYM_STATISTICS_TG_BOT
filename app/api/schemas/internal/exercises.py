"""DTO-схемы internal API для упражнений Telegram-бота."""

from pydantic import BaseModel, ConfigDict


class InternalBotExerciseResponse(BaseModel):
    """Упражнение из справочника для сценариев Telegram-бота."""

    id: int
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)
