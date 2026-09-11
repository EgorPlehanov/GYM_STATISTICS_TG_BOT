"""DTO-схемы API-клиента Telegram-бота для статистики."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BotExerciseRating:
    """Рейтинг пользователя по упражнению, полученный через backend API.

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
    rating_value: float
