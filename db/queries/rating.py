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
            record.rating_value = max_weight
        else:
            record = UserExerciseRating(
                user_id = user_id,
                exercise_id = exercise_id,
                exercise_rank_id = exercise_rank_id,
                rating_value = max_weight
            )
        session.add(record)

    await session.commit()



StatisticData = namedtuple('statistic', [
    'exercise_id', 'exercise_name', 'rank_name', 'rank_level', 'rating_value'
])

async def get_user_exercise_rating(
    session: AsyncSession,
    user_id: int
) -> List[StatisticData]:
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
    return [StatisticData(*row) for row in result.all()]



ExportData = namedtuple('export_data', [
# Set current
    'date',
    'comment',
    'exercise_name',
    'overall_order',
    'exercise_order',
    'weight',
    'repetitions',
# Training current
    'training_exercise_weight_sum',
    'training_exercise_repetitions_sum',
    'training_exercise_sets_count',
    'training_sets_count',
# Exercise all
    'exercise_all_weight_sum',
    'exercise_all_repetitions_sum',
    'exercise_all_sets_count',
# Exercise rank
    'exercise_rank_value',
    'exercise_rank_name',
    'exercise_rank_star_count',
    'exercise_rank_star_level',
# All
    'all_sets_count'
])

async def get_export_data(
    session: AsyncSession,
    user_id: int
) -> List[ExportData]:
    """
    Возвращает данные для экспорта
    """
    result = await session.execute(
        select(
            # Set current
            Training.date.cast(Date).label('date'),         # Дата тренировки
            Training.comment.label('comment'),              # Комментарий
            Exercise.name.label('exercise_name'),           # Название упражнения
            Set.overall_order.label('overall_order'),       # № подхода в тренировке
            Set.exercise_order.label('exercise_order'),     # № подхода в упражнении на тренировке
            Set.weight.label('weight'),                     # Вес в подходе
            Set.repetitions.label('repetitions'),           # Повторения в подходе
            # Training current
            func.sum(Set.weight * Set.repetitions).over(    # Сумма весов всех подходов упражнения на тренировке
                partition_by = [Training.id, Exercise.id],
            ),
            func.sum(Set.repetitions).over(                 # Сумма повторений всех подходов упражнения на тренировке
                partition_by = [Training.id, Exercise.id],
            ),
            func.count().over(                              # Количество подходов упражнения на тренировке
                partition_by = [Training.id, Exercise.id],
            ),
            func.count().over(                              # Количество подходов на тренировке
                partition_by = [Training.id],
            ),
            # Exercise all
            func.sum(Set.weight * Set.repetitions).over(    # Сумма весов всех подходов упражнения всех тренировок
                partition_by = [Exercise.id],
            ),
            func.sum(Set.repetitions).over(                 # Сумма повторений всех подходов упражнения всех тренировок
                partition_by = [Exercise.id],
            ),
            func.count().over(                              # Количество подходов упражнения всех тренировок
                partition_by = [Exercise.id],
            ),
            # Exercise rank
            UserExerciseRating.rating_value.label('exercise_rank_value'),  # максимальное значение веса в упражнении
            Rank.name.label('exercise_rank_name'),                         # Название ранга в упражнении
            ExerciseRank.level.label('exercise_rank_star_count'),          # Количество звезд в ранге в упражнении
            func.repeat('⭐', ExerciseRank.level).label('exercise_rank_star_level'),  # Звезды в ранге в упражнении
            # All
            func.count().over(                              # Количество подходов всех тренировок
                partition_by = [],
            ),
        )
        .join (Set, Set.training_id == Training.id)
        .join (Exercise, Exercise.id == Set.exercise_id)
        .outerjoin(UserExerciseRating, and_(
            UserExerciseRating.exercise_id == Set.exercise_id,
            UserExerciseRating.user_id == Training.user_id
        ))
        .join(ExerciseRank, ExerciseRank.id == UserExerciseRating.exercise_rank_id)
        .join(Rank, Rank.id == ExerciseRank.rank_id)
        .where(Training.user_id == user_id)
        .order_by(Training.date.cast(Date), Exercise.name, Set.exercise_order)
    )
    return [ExportData(*row) for row in result.all()]
