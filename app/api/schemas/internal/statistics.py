"""DTO-схемы internal API для статистики Telegram-бота."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InternalBotExerciseRatingResponse(BaseModel):
    """Рейтинг пользователя по упражнению для Telegram-бота.

    Attributes:
        exercise_id: внутренний id упражнения.
        exercise_name: название упражнения.
        rank_name: название ранга.
        rank_level: уровень ранга для упражнения.
        rating_value: значение, по которому рассчитан рейтинг.
    """

    exercise_id: int
    exercise_name: str
    rank_name: str
    rank_level: int
    rating_value: Decimal

    model_config = ConfigDict(from_attributes=True)
