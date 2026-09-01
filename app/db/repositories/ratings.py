"""Репозиторий рейтингов."""

from collections import namedtuple

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Exercise, ExerciseRank, Rank, Training, UserExerciseRating
from app.db.repositories.users import get_internal_user_id_by_telegram_id


class RatingRepository:
    """Доступ к данным пользовательских рейтингов."""


StatisticData = namedtuple(
    "statistic",
    ["exercise_id", "exercise_name", "rank_name", "rank_level", "rating_value"],
)


async def update_or_create_user_exercise_rating(
    session: AsyncSession,
    user_id: int,
) -> None:
    """Обновляет или создает рейтинги пользователя.

    `user_id` - Telegram user id. Расчет выполняется по внутреннему `User.id`.
    """
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return

    sql_expression = text(
        """
        WITH sd AS (
            SELECT
                t.user_id,
                s.training_id,
                s.exercise_id,
                MAX(s.weight) AS max_weight
            FROM set s
                JOIN training t ON t.id = s.training_id
            WHERE t.user_id = :user_id
              AND s.repetitions > 0
            GROUP BY t.user_id, s.training_id, s.exercise_id, s.weight
        )
        SELECT
            q.exercise_id,
            q.exercise_rank_id,
            q.max_weight
        FROM (
            SELECT
                sd.exercise_id,
                er.id AS exercise_rank_id,
                sd.max_weight,
                ROW_NUMBER() OVER (
                    PARTITION BY sd.exercise_id
                    ORDER BY r.grade DESC, er.level DESC
                ) AS rn
            FROM sd
                LEFT JOIN exercise_rank er ON sd.exercise_id = er.exercise_id OR (
                    SELECT 1 FROM exercise_rank WHERE sd.exercise_id = exercise_id LIMIT 1
                ) IS NULL AND er.is_default
                JOIN rank r ON r.id = er.rank_id
            WHERE er.grade_threshold <= sd.max_weight
        ) q
        WHERE q.rn = 1
        """
    )

    new_ratings = await session.execute(sql_expression, {"user_id": internal_user_id})

    for exercise_id, exercise_rank_id, max_weight in new_ratings.fetchall():
        record = await session.scalar(
            select(UserExerciseRating).where(
                UserExerciseRating.user_id == internal_user_id,
                UserExerciseRating.exercise_id == exercise_id,
            )
        )
        if record:
            record.exercise_rank_id = exercise_rank_id
            record.rating_value = max_weight
        else:
            record = UserExerciseRating(
                user_id=internal_user_id,
                exercise_id=exercise_id,
                exercise_rank_id=exercise_rank_id,
                rating_value=max_weight,
            )
        session.add(record)

    await session.commit()


async def get_user_exercise_rating(
    session: AsyncSession,
    user_id: int,
) -> list[StatisticData]:
    """Возвращает рейтинг пользователя с Telegram id."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return []

    result = await session.execute(
        select(
            Exercise.id.label("exercise_id"),
            Exercise.name.label("exercise_name"),
            Rank.name.label("rank_name"),
            ExerciseRank.level.label("rank_level"),
            UserExerciseRating.rating_value,
        )
        .join(Exercise, Exercise.id == UserExerciseRating.exercise_id)
        .join(ExerciseRank, ExerciseRank.id == UserExerciseRating.exercise_rank_id)
        .join(Rank, Rank.id == ExerciseRank.rank_id)
        .where(UserExerciseRating.user_id == internal_user_id)
        .order_by(Rank.grade.desc(), ExerciseRank.level.desc())
    )
    return [StatisticData(*row) for row in result.all()]


async def has_rating_for_training_user_and_exercise(
    session: AsyncSession,
    training_id: int,
    exercise_id: int,
) -> bool:
    """Проверяет, есть ли рейтинг для пользователя тренировки и упражнения."""
    result = await session.execute(
        select(UserExerciseRating.id)
        .join(Training, Training.user_id == UserExerciseRating.user_id)
        .where(
            Training.id == training_id,
            UserExerciseRating.exercise_id == exercise_id,
        )
    )
    return result.first() is not None
