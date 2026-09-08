"""Репозиторий тренировок."""

from datetime import datetime

from sqlalchemy import Date, and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Exercise, Set, Training, User
from app.db.repositories.users import get_internal_user_id_by_telegram_id


class TrainingRepository:
    """Доступ к данным тренировок и подходов."""


SetData = dict[str, int | float | datetime | str]
ExerciseData = dict[str, str | int | dict[int, SetData]]
TrainingData = dict[str, int | datetime | str | dict[int, ExerciseData]]


async def get_sorted_exercises_by_sets_count(
    session: AsyncSession,
    user_id: int,
    page_size: int = 5,
    page_num: int = 0,
    substring: str | None = None,
) -> list[Exercise]:
    """Возвращает упражнения, отсортированные по частоте использования пользователем.

    `user_id` сохраняет старый контракт бота и означает Telegram user id.
    """
    subquery = (
        select(Set.id.label("set_id"), Set.exercise_id)
        .join(Training)
        .join(User)
        .filter(User.telegram_id == user_id)
        .subquery()
    )

    stmt = (
        select(Exercise)
        .outerjoin(subquery, subquery.c.exercise_id == Exercise.id)
        .group_by(Exercise.id)
        .order_by(
            func.count(subquery.c.set_id).desc(),
            Exercise.name,
        )
        .limit(page_size)
        .offset(page_size * page_num)
    )

    if substring is not None:
        substring = substring.lower()
        stmt = stmt.filter(
            or_(
                func.lower(Exercise.name).contains(substring),
                func.lower(Exercise.description).contains(substring),
            )
        )

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_exercises_weight_repetitions_modes(
    session: AsyncSession,
    user_id: int,
    last_training_count: int = 12,
) -> dict[int, dict[str, int | dict[str, int | float]]]:
    """Возвращает модальные вес и повторения по подходам последних тренировок.

    `user_id` - Telegram user id. Если пользователь не найден, возвращается пустой словарь.
    """
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return {}

    result = await session.execute(
        select(
            Set.exercise_id,
            Set.exercise_order,
            func.mode().within_group(Set.weight.desc()).label("weight_mode"),
            func.mode().within_group(Set.repetitions.desc()).label("repetitions_mode"),
            func.max(Set.exercise_order)
            .over(partition_by=Set.exercise_id)
            .label("max_exercise_order"),
        )
        .where(
            Set.training_id.in_(
                select(Training.id)
                .where(Training.user_id == internal_user_id)
                .order_by(Training.date.desc())
                .limit(last_training_count)
            )
        )
        .group_by(Set.exercise_id, Set.exercise_order)
        .order_by(Set.exercise_id, Set.exercise_order)
    )

    weight_repetitions_modes = {}
    for row in result.all():
        if row.exercise_id not in weight_repetitions_modes:
            weight_repetitions_modes[row.exercise_id] = {
                "max_exercise_order": row.max_exercise_order,
                "sets_modes": {},
            }
        weight_repetitions_modes[row.exercise_id]["sets_modes"][row.exercise_order] = {
            "weight_mode": row.weight_mode,
            "repetitions_mode": row.repetitions_mode,
        }
    return weight_repetitions_modes


async def save_new_set_data(
    session: AsyncSession,
    training_id: int,
    exercise_id: int,
    local_number: int,
    set_data: SetData,
) -> int:
    """Сохраняет новый подход и возвращает его id."""
    new_set = Set(
        training_id=training_id,
        exercise_id=exercise_id,
        overall_order=set_data["set_number"],
        exercise_order=local_number,
        weight=set_data["weight"],
        repetitions=set_data["repetitions"],
        execution_time=set_data["time"].replace(tzinfo=None),
    )
    session.add(new_set)
    await session.flush()
    return new_set.id


async def update_set_data(
    session: AsyncSession,
    exercise_order: int,
    set_data: SetData,
) -> bool:
    """Обновляет подход и возвращает признак изменения строки."""
    result = await session.execute(
        update(Set)
        .values(
            weight=set_data.get("weight"),
            repetitions=set_data.get("repetitions"),
            overall_order=set_data.get("set_number"),
            exercise_order=exercise_order,
        )
        .where(
            Set.id == set_data.get("id"),
            or_(
                Set.weight != set_data.get("weight"),
                Set.repetitions != set_data.get("repetitions"),
                Set.overall_order != set_data.get("set_number"),
                Set.exercise_order != exercise_order,
            ),
        )
    )
    return result.rowcount > 0


async def delete_old_sets(
    session: AsyncSession,
    training_id: int,
    current_sets_id: list[int],
) -> bool:
    """Удаляет подходы тренировки, которых нет в текущем наборе данных."""
    result = await session.execute(
        delete(Set)
        .where(
            and_(
                Set.training_id == training_id,
                Set.id.not_in(current_sets_id),
            )
        )
        .returning(Set.id)
    )
    return sum(1 for _ in result.scalars()) > 0


async def save_new_training_data(
    session: AsyncSession,
    training_data: TrainingData,
) -> int:
    """Сохраняет новую тренировку и возвращает ее id."""
    internal_user_id = await get_internal_user_id_by_telegram_id(
        session,
        training_data.get("user_id"),
    )
    if internal_user_id is None:
        raise ValueError("Пользователь для тренировки не найден")

    training = Training(
        user_id=internal_user_id,
        date=training_data.get("date").replace(tzinfo=None),
        comment=training_data.get("comment"),
    )
    session.add(training)
    await session.flush()
    return training.id


async def update_training_data(
    session: AsyncSession,
    training_data: TrainingData,
) -> bool:
    """Обновляет тренировку и возвращает признак изменения строки."""
    result = await session.execute(
        update(Training)
        .values(
            date=training_data.get("date").replace(tzinfo=None),
            comment=training_data.get("comment"),
        )
        .where(
            Training.id == training_data.get("id"),
            or_(
                Training.date.cast(Date) != training_data.get("date").date(),
                Training.comment != training_data.get("comment"),
                and_(
                    Training.comment.is_(None),
                    training_data.get("comment") is not None,
                ),
            ),
        )
    )
    return result.rowcount > 0


async def save_training_data(
    session: AsyncSession,
    training_data: TrainingData,
) -> tuple[int, bool, bool]:
    """Сохраняет тренировку и подходы.

    Returns:
        `(training_id, update_flag, create_flag)`, где `update_flag` показывает,
        были ли изменены данные, а `create_flag` - создана ли новая тренировка.
    """
    update_flag = False
    create_flag = False

    training_id = training_data.get("id")
    if training_id is None:
        training_id = await save_new_training_data(session, training_data)
        create_flag = True
    else:
        is_updated = await update_training_data(session, training_data)
        update_flag = is_updated if is_updated else update_flag

    sets_id = []
    exercises = training_data.get("exercises")
    for exercise_id, exercise_data in exercises.items():
        sets = exercise_data["sets"]

        for local_number, set_data in sets.items():
            set_id = set_data.get("id")
            if set_id is None:
                set_id = await save_new_set_data(
                    session,
                    training_id,
                    exercise_id,
                    local_number,
                    set_data,
                )
                update_flag = True
            else:
                is_updated = await update_set_data(session, local_number, set_data)
                update_flag = is_updated if is_updated else update_flag

            sets_id.append(set_id)

    is_updated = await delete_old_sets(session, training_id, sets_id)
    update_flag = is_updated if is_updated else update_flag

    await session.commit()
    return training_id, update_flag, create_flag


async def check_training_exists_for_user_and_date(
    session: AsyncSession,
    user_id: int,
    date: datetime,
) -> bool:
    """Проверяет, есть ли тренировка пользователя с Telegram id за указанную дату."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return False

    result = await session.execute(
        select(Training).filter(
            Training.user_id == internal_user_id,
            func.date(Training.date) == date.date(),
        )
    )
    return bool(result.scalar())


async def get_training_data_by_date_and_user(
    session: AsyncSession,
    user_id: int,
    date: datetime,
) -> TrainingData:
    """Возвращает данные тренировки пользователя с Telegram id за дату."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        raise ValueError("Пользователь для получения тренировки не найден")

    training_result = await session.execute(
        select(
            Training.id.label("id"),
            Training.comment.label("comment"),
        ).filter(
            Training.user_id == internal_user_id,
            func.date(Training.date) == date.date(),
        )
    )
    training_result = training_result.first()
    if training_result is None:
        raise ValueError("Тренировка за указанную дату не найдена")

    sets_result = await session.execute(
        select(
            Set.id.label("set_id"),
            Set.exercise_id.label("exercise_id"),
            Exercise.name.label("exercise_name"),
            Set.overall_order.label("overall_order"),
            Set.exercise_order.label("exercise_order"),
            Set.weight.label("weight"),
            Set.repetitions.label("repetitions"),
            Set.execution_time.label("execution_time"),
        )
        .join(Exercise, Exercise.id == Set.exercise_id)
        .filter(Set.training_id == training_result.id)
        .order_by(Set.overall_order)
    )

    training_data = {
        "id": training_result.id,
        "user_id": user_id,
        "date": date,
        "comment": training_result.comment,
        "global_set_counter": 0,
        "exercises": {},
    }
    overall_order = 0
    for row in sets_result:
        (
            set_id,
            exercise_id,
            exercise_name,
            overall_order,
            exercise_order,
            weight,
            repetitions,
            execution_time,
        ) = row

        if exercise_id not in training_data["exercises"]:
            training_data["exercises"][exercise_id] = {
                "exercise_name": exercise_name,
                "local_set_counter": 0,
                "sets": {},
            }

        training_data["exercises"][exercise_id]["sets"][exercise_order] = {
            "id": set_id,
            "set_number": overall_order,
            "weight": weight,
            "repetitions": repetitions,
            "time": execution_time,
        }

    training_data["global_set_counter"] = overall_order

    for exercise in training_data["exercises"].values():
        exercise["local_set_counter"] = max(exercise["sets"].keys())

    return training_data


async def delete_training_by_id(
    session: AsyncSession,
    training_id: int,
) -> None:
    """Удаляет тренировку по id."""
    await session.execute(delete(Training).where(Training.id == training_id))
    await session.commit()


async def get_training_date_by_user_id(
    session: AsyncSession,
    user_id: int,
) -> list[datetime]:
    """Возвращает даты тренировок пользователя с Telegram id."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return []

    result = await session.execute(
        select(Training.date)
        .filter(Training.user_id == internal_user_id)
        .order_by(Training.date)
    )
    return [row[0].date() for row in result.all()]
