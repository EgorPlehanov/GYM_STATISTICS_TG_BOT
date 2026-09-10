"""Internal endpoints статистики для Telegram-бота."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.schemas.internal.statistics import InternalBotExerciseRatingResponse
from app.domain.statistics.service import get_user_exercise_rating

router = APIRouter()


@router.get(
    "/bot/statistics/exercise-rating",
    response_model=list[InternalBotExerciseRatingResponse],
)
async def get_bot_user_exercise_rating(
    session: DbSession,
    telegram_id: int,
) -> list[InternalBotExerciseRatingResponse]:
    """Возвращает рейтинг упражнений пользователя для Telegram-бота.

    Args:
        telegram_id: Telegram user id пользователя.

    Returns:
        список рейтингов упражнений пользователя.
    """
    return await get_user_exercise_rating(session=session, user_id=telegram_id)
