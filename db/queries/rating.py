from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, update, delete, func, Date, or_, and_

from typing import List
from datetime import datetime, timedelta, date
from collections import namedtuple

from ..models import Rank, ExerciseRank, UserExerciseRating, User, Set, Training, Exercise



async def update_or_create_user_exercise_rating(
    session: AsyncSession,
    user_id: int,
):
    """
    Обновляет или создает рейтинг пользователя
    """
    sql_expression = text("""
        WITH sd AS (
            SELECT
                t.user_id,
                s.training_id,
                s.exercise_id,
                MAX(s.weight) AS max_weight
            FROM set s
                JOIN training t ON t.id = s.training_id
            WHERE t.user_id = :user_id
            
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
                ROW_NUMBER() OVER (PARTITION BY sd.exercise_id ORDER BY r.grade DESC, er.level DESC) AS rn
            FROM sd
                LEFT JOIN exercise_rank er ON sd.exercise_id = er.exercise_id OR (
                    SELECT 1 FROM exercise_rank WHERE sd.exercise_id = exercise_id LIMIT 1
                ) IS NULL AND er.is_default
                JOIN rank r ON r.id = er.rank_id
            WHERE er.grade_threshold <= sd.max_weight
        ) q
        WHERE q.rn = 1
    """)
    params = {
        'user_id': user_id,
        # 'start_date': datetime(2024, 1, 1),
        # 'end_date': datetime(2024, 1, 5)
        # --AND t.date BETWEEN :start_date AND :end_date
    }

    new_ratings = await session.execute(
        sql_expression,
        params
    )

    for exercise_id, exercise_rank_id, max_weight in new_ratings.fetchall():
        record = await session.scalar(
            select(UserExerciseRating).where(
                UserExerciseRating.user_id == user_id,
                UserExerciseRating.exercise_id == exercise_id
            )
        )
        if record:
            record.exercise_rank_id = exercise_rank_id
        else:
            record = UserExerciseRating(
                user_id = user_id,
                exercise_id = exercise_id,
                exercise_rank_id = exercise_rank_id,
                rating_value = max_weight
            )
        session.add(record)

    await session.commit()



statistic = namedtuple('statistic', ['exercise_id', 'exercise_name', 'rank_name', 'rank_level', 'rating_value'])

async def get_user_exercise_rating(
    session: AsyncSession,
    user_id: int
) -> List[statistic]:
    """
    Возвращает рейтинг пользователя
    """
    result = await session.execute(
        select(
            Exercise.id.label('exercise_id'),
            Exercise.name.label('exercise_name'),
            Rank.name.label('rank_name'),
            ExerciseRank.level.label('rank_level'),
            UserExerciseRating.rating_value
        )
        .join(Exercise, Exercise.id == UserExerciseRating.exercise_id)
        .join(ExerciseRank, ExerciseRank.id == UserExerciseRating.exercise_rank_id)
        .join(Rank, Rank.id == ExerciseRank.rank_id)
        .where(UserExerciseRating.user_id == user_id)
        .order_by(Rank.grade.desc(), ExerciseRank.level.desc())
    )
    return [
        statistic(*row) for row in result.all()
    ]