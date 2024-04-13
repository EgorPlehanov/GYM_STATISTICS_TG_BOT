from sqlalchemy import func, select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List, Dict, Union
from datetime import datetime

from ..models import Exercise, Set, Training, GroupTrainingResultMessage



async def get_sorted_exercises_by_sets_count(
    session: AsyncSession,
    user_id: int,
    page_size: int = 5,
    page_num: int = 0
) -> List[Exercise]:
    """
    Возвращает список упражнений по количеству подходов
    """
    offset = (page_num - 1) * page_size

    result = await session.execute(select(Exercise))
    all_exercises = result.scalars().all()
    return all_exercises

    exercise_sets_count = await session.execute(
        select(
            Set.exercise_id,
            func.count(Set.id).label('set_count')
        )
        .join(Training, Training.id == Set.training_id)
        .filter(Training.user_id == user_id)
        .group_by(Set.exercise_id)
        .order_by(func.count(Set.id).desc())
    )

    sorted_exercises = []
    async for exercise_id, set_count in exercise_sets_count:
        exercise = await session.execute(
            select(Exercise.id, Exercise.name)
            .filter(Exercise.id == exercise_id)
        ).first()
        sorted_exercises.append(ExerciseSetCount(
            id=exercise.id, name=exercise.name, count=set_count
        ))

    return sorted_exercises



SetData = Dict[str, Union[int, float, datetime, str]]  # Тип для данных о подходе
ExerciseData = Dict[str, Union[str, int, Dict[int, SetData]]]  # Тип для данных об упражнении
TrainingData = Dict[str, Union[int, Dict[int, ExerciseData]]]  # Тип для данных о тренировке


async def save_new_set_data(
    session: AsyncSession,
    training_id: int,
    exercise_id: int,
    local_number: int,
    set_data: SetData
) -> int:
    """
    Сохраняет данные о подходе в базу данных
    """
    global_number = set_data['set_number']
    weight = set_data['weight']
    repetitions = set_data['repetitions']
    execution_time = set_data['time'].replace(tzinfo=None)
    
    new_set = Set(
        training_id=training_id,
        exercise_id=exercise_id,
        overall_order=global_number,
        exercise_order=local_number,
        weight=weight,
        repetitions=repetitions,
        execution_time=execution_time
    )
    session.add(new_set)
    await session.flush()
    return new_set.id


async def update_set_data(
    session: AsyncSession,
    set_data: SetData
) -> None:
    """
    Обновляет данные о подходе
    """
    set_id = set_data.get('id')
    await session.execute(
        update(Set)
        .values(
            weight=set_data.get('weight'),
            repetitions=set_data.get('repetitions'),
        )
        .where(Set.id == set_id)
    )


async def delete_old_sets(
    session: AsyncSession,
    training_id: int,
    current_sets_id: List[int]
) -> None:
    """
    Удаляет старые данные о подходах
    """
    await session.execute(
        delete(Set)
        .where(and_(
            Set.training_id == training_id,
            Set.id.not_in(current_sets_id)
        ))
    )


async def save_new_training_data(
    session: AsyncSession,
    training_data: TrainingData
) -> None:
    """
    Сохраняет данные о тренировке в базу данных
    """
    training = Training(
        user_id = training_data.get('user_id'),
        date = training_data.get('date').replace(tzinfo=None),
        comment = training_data.get('comment'),
    )
    session.add(training)
    await session.flush()  # для получения training.id
    return training.id


async def update_training_data(
    session: AsyncSession,
    training_data: TrainingData
) -> int:
    """
    Обновляет данные о тренировке
    """
    training_id = training_data.get('id')
    await session.execute(
        update(Training)
        .values(
            date = training_data.get('date').replace(tzinfo=None),
            comment = training_data.get('comment'),
        )
        .where(Training.id == training_id)
    )


async def save_training_data(
    session: AsyncSession,
    training_data: TrainingData
) -> tuple[int, bool]:
    """
    Сохраняет данные о тренировке в базу данных    
    """
    update_flag = False

    training_id = training_data.get('id')
    if training_id is not None:
        update_flag = True
        await update_training_data(session, training_data)
    else:
        training_id = await save_new_training_data(session, training_data)

    sets_id = []
    exercises = training_data.get('exercises')
    for exercise_id, exercise_data in exercises.items():
        sets = exercise_data['sets']
        
        for local_number, set_data in sets.items():
            set_id = set_data.get('id')
            if set_id is None:
                set_id = await save_new_set_data(session, training_id, exercise_id, local_number, set_data)
            else:
                update_flag = True
                await update_set_data(session, set_data)
            sets_id.append(set_id)

    await delete_old_sets(session, training_id, sets_id)
    await session.commit()

    return training_id, update_flag
    


async def check_training_exists_for_user_and_date(
    session: AsyncSession,
    user_id: int,
    date: datetime
) -> bool:
    """
    Проверяет существует ли тренировка для пользователя и даты
    """
    result = await session.execute(
        select(Training)
        .filter(Training.user_id == user_id, func.date(Training.date) == date.date())
    )
    return bool(result.scalar())


async def get_training_data_by_date_and_user(
    session: AsyncSession, user_id:
    int, date: datetime
) -> TrainingData:
    """
    Возвращает данные о тренировке по дате и пользователям
    """
    training_result = await session.execute(
        select(
            Training.id.label('id'),
            Training.comment.label('comment')
        )
        .filter(Training.user_id == user_id, func.date(Training.date) == date.date())
    )
    training_result = training_result.first()

    sets_result = await session.execute(
        select(
            Set.id.label('set_id'),
            Set.exercise_id.label('exercise_id'),
            Exercise.name.label('exercise_name'),
            Set.overall_order.label('overall_order'),
            Set.exercise_order.label('exercise_order'),
            Set.weight.label('weight'),
            Set.repetitions.label('repetitions'),
            Set.execution_time.label('execution_time')
        )
        .join(Exercise, Exercise.id == Set.exercise_id)
        .filter(Set.training_id == training_result.id)
        .order_by(Set.overall_order)
    )
    
    training_data = {
        'id': training_result.id,
        'user_id': user_id,
        'date': date,
        'comment': training_result.comment,
        'global_set_counter': 0,
        'exercises': {}
    }
    for row in sets_result:
        set_id, exercise_id, exercise_name, overall_order, exercise_order, weight, repetitions, execution_time = row
        
        if exercise_id not in training_data['exercises']:
            training_data['exercises'][exercise_id] = {
                'exercise_name': exercise_name,
                'local_set_counter': 0,
                'sets': {}
            }
        
        training_data['exercises'][exercise_id]['local_set_counter'] += 1
        training_data['global_set_counter'] += 1
        
        training_data['exercises'][exercise_id]['sets'][overall_order] = {
            'id': set_id,
            'set_number': exercise_order,
            'weight': weight,
            'repetitions': repetitions,
            'time': execution_time
        }
    return training_data



async def delete_training_by_id(
    session: AsyncSession,
    training_id: int
) -> None:
    """
    Удаляет тренировку по id
    """
    await session.execute(delete(Training).where(Training.id == training_id))
    await session.commit()



async def get_training_date_by_user_id(
    session: AsyncSession,
    user_id: int
) -> List[datetime]:
    """
    Возвращает список дат тренировок пользователя
    """
    result = await session.execute(
        select(Training.date)
        .filter(Training.user_id == user_id)
        .order_by(Training.date)
    )
    return [row[0].date() for row in result.all()]