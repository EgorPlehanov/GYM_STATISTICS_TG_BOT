"""Сервис тренировок."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Exercise
from app.db.repositories import exercises as exercise_repository
from app.db.repositories import trainings as training_repository

from .schemas import TrainingSaveOutcome


class TrainingsService:
    """Бизнес-сценарии для тренировок."""

    get_sorted_exercises_by_sets_count = staticmethod(
        training_repository.get_sorted_exercises_by_sets_count
    )
    get_exercise_by_id = staticmethod(exercise_repository.get_exercise_by_id)
    check_training_exists_for_user_and_date = staticmethod(
        training_repository.check_training_exists_for_user_and_date
    )
    get_training_data_by_date_and_user = staticmethod(
        training_repository.get_training_data_by_date_and_user
    )
    delete_training_by_id = staticmethod(training_repository.delete_training_by_id)
    get_training_date_by_user_id = staticmethod(training_repository.get_training_date_by_user_id)


SetData = training_repository.SetData
ExerciseData = training_repository.ExerciseData
TrainingData = training_repository.TrainingData


async def get_sorted_exercises_by_sets_count(
    session: AsyncSession,
    user_id: int,
    page_size: int = 5,
    page_num: int = 0,
    substring: str | None = None,
) -> list[Exercise]:
    """Возвращает упражнения, отсортированные по частоте использования пользователем."""
    return await training_repository.get_sorted_exercises_by_sets_count(
        session,
        user_id,
        page_size,
        page_num,
        substring,
    )


async def get_exercises_weight_repetitions_modes(
    session: AsyncSession,
    user_id: int,
    last_training_count: int = 12,
) -> dict[int, dict]:
    """Возвращает рассчитанные подсказки веса и повторений.

    Args:
        session: активная сессия базы данных.
        user_id: Telegram user id владельца тренировок.
        last_training_count: число последних тренировок для расчета моды.

    Returns:
        read-структуру подсказок по упражнениям и номерам подходов.
    """
    return await training_repository.get_exercises_weight_repetitions_modes(
        session,
        user_id,
        last_training_count,
    )


async def get_exercise_by_id(session: AsyncSession, exercise_id: int) -> Exercise | None:
    """Возвращает упражнение по id."""
    return await exercise_repository.get_exercise_by_id(session, exercise_id)


async def save_training(
    session: AsyncSession,
    training_data: TrainingData,
    replace_training_id: int | None = None,
) -> tuple[int, TrainingSaveOutcome, list[tuple[int, int]]]:
    """Сохраняет тренировку и возвращает единый бизнес-результат операции.

    Args:
        session: активная сессия базы данных.
        training_data: данные тренировки в текущем формате репозитория.
        replace_training_id: id конфликтующей тренировки для атомарной замены.

    Returns:
        id тренировки, семантический результат сохранения и redirect-сообщения
        удаленной конфликтующей тренировки.
        Создание тренировки имеет приоритет над техническими изменениями
        созданных вместе с ней подходов.
    """
    (
        training_id,
        updated,
        created,
        deleted_redirect_messages,
    ) = await training_repository.save_training_data(
        session,
        training_data,
        replace_training_id=replace_training_id,
    )
    if created:
        return training_id, TrainingSaveOutcome.CREATED, deleted_redirect_messages
    if updated:
        return training_id, TrainingSaveOutcome.UPDATED, deleted_redirect_messages
    return training_id, TrainingSaveOutcome.UNCHANGED, deleted_redirect_messages


async def check_training_exists_for_user_and_date(
    session: AsyncSession,
    user_id: int,
    date: date,
) -> bool:
    """Проверяет, есть ли тренировка пользователя за указанную дату."""
    return await training_repository.check_training_exists_for_user_and_date(session, user_id, date)


async def get_training_data_by_date_and_user(
    session: AsyncSession,
    user_id: int,
    date: date,
) -> TrainingData:
    """Возвращает данные тренировки пользователя за дату."""
    return await training_repository.get_training_data_by_date_and_user(session, user_id, date)


async def delete_training_by_id(session: AsyncSession, training_id: int) -> None:
    """Удаляет тренировку по id."""
    await training_repository.delete_training_by_id(session, training_id)


async def get_training_date_by_user_id(session: AsyncSession, user_id: int) -> list[date]:
    """Возвращает даты тренировок пользователя."""
    return await training_repository.get_training_date_by_user_id(session, user_id)
