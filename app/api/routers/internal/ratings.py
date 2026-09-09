"""Internal endpoints для сценариев рейтингов Telegram-бота."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.domain.ratings.service import update_or_create_user_exercise_rating

router = APIRouter()


@router.post("/bot/users/{telegram_id}/rating/recalculate")
async def recalculate_bot_user_rating(
    telegram_id: int,
    session: DbSession,
) -> dict[str, str]:
    """Пересчитывает рейтинги пользователя после сохранения тренировки.

    Args:
        telegram_id: Telegram user id пользователя.

    Returns:
        короткий статус успешного выполнения операции.
    """
    await update_or_create_user_exercise_rating(
        session=session,
        user_id=telegram_id,
    )
    return {"status": "ok"}
