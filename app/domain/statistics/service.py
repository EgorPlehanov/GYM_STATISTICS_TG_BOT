"""Сервис статистики."""


from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import ratings as rating_repository


class StatisticsService:
    """Бизнес-сценарии для статистики."""

    get_user_exercise_rating = staticmethod(rating_repository.get_user_exercise_rating)


StatisticData = rating_repository.StatisticData


async def get_user_exercise_rating(
    session: AsyncSession,
    user_id: int,
) -> list[StatisticData]:
    """Возвращает рейтинг пользователя для отображения в статистике."""
    return await rating_repository.get_user_exercise_rating(session, user_id)
