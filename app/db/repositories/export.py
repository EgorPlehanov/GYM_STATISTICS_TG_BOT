"""Репозиторий экспорта."""

from collections import namedtuple

from sqlalchemy import Date, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Exercise, ExerciseRank, Rank, Set, Training, UserExerciseRating
from app.db.repositories.users import get_internal_user_id_by_telegram_id


class ExportRepository:
    """Доступ к данным для экспорта."""


ExportData = namedtuple(
    "export_data",
    [
        "date",
        "comment",
        "exercise_name",
        "overall_order",
        "exercise_order",
        "weight",
        "repetitions",
        "training_exercise_weight_sum",
        "training_exercise_repetitions_sum",
        "training_exercise_sets_count",
        "training_sets_count",
        "exercise_all_weight_sum",
        "exercise_all_repetitions_sum",
        "exercise_all_sets_count",
        "exercise_rank_value",
        "exercise_rank_name",
        "exercise_rank_star_count",
        "exercise_rank_star_level",
        "all_sets_count",
    ],
)


async def get_export_data(
    session: AsyncSession,
    user_id: int,
) -> list[ExportData]:
    """Возвращает данные для экспорта тренировок пользователя с Telegram id."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return []

    result = await session.execute(
        select(
            Training.date.cast(Date).label("date"),
            Training.comment.label("comment"),
            Exercise.name.label("exercise_name"),
            Set.overall_order.label("overall_order"),
            Set.exercise_order.label("exercise_order"),
            Set.weight.label("weight"),
            Set.repetitions.label("repetitions"),
            func.sum(Set.weight * Set.repetitions).over(
                partition_by=[Training.id, Exercise.id],
            ),
            func.sum(Set.repetitions).over(
                partition_by=[Training.id, Exercise.id],
            ),
            func.count().over(
                partition_by=[Training.id, Exercise.id],
            ),
            func.count().over(
                partition_by=[Training.id],
            ),
            func.sum(Set.weight * Set.repetitions).over(
                partition_by=[Exercise.id],
            ),
            func.sum(Set.repetitions).over(
                partition_by=[Exercise.id],
            ),
            func.count().over(
                partition_by=[Exercise.id],
            ),
            UserExerciseRating.rating_value.label("exercise_rank_value"),
            Rank.name.label("exercise_rank_name"),
            ExerciseRank.level.label("exercise_rank_star_count"),
            func.repeat("⭐", ExerciseRank.level).label("exercise_rank_star_level"),
            func.count().over(partition_by=[]),
        )
        .join(Set, Set.training_id == Training.id)
        .join(Exercise, Exercise.id == Set.exercise_id)
        .outerjoin(
            UserExerciseRating,
            and_(
                UserExerciseRating.exercise_id == Set.exercise_id,
                UserExerciseRating.user_id == Training.user_id,
            ),
        )
        .join(ExerciseRank, ExerciseRank.id == UserExerciseRating.exercise_rank_id)
        .join(Rank, Rank.id == ExerciseRank.rank_id)
        .where(Training.user_id == internal_user_id)
        .order_by(Training.date.cast(Date), Exercise.name, Set.exercise_order)
    )
    return [ExportData(*row) for row in result.all()]
