from sqlalchemy import func, select, update, delete, and_, or_, Date
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List, Dict, Union
from datetime import datetime

from ..models import Exercise, Set, Training, User



async def get_sorted_exercises_by_sets_count(
    session: AsyncSession,
    user_id: int,
    page_size: int = 5,
    page_num: int = 0,
    substring: str = None,
) -> List[Exercise]:
    """
    Возвращает список упражнений по количеству подходов
    """
    subquery = (
        select(Set.id.label('set_id'), Set.exercise_id)
        .join(Training)
        .join(User)
        .filter(User.id == user_id)
        .subquery()
    )

    stmt = (
        select(
            Exercise,
        )
        .outerjoin(subquery, subquery.c.exercise_id == Exercise.id)
        .group_by(Exercise.id)
        .order_by(
            func.count(subquery.c.set_id).desc(),
            Exercise.name
        )
        .limit(page_size)
        .offset(page_size * page_num)
    )

    if substring is not None:
        substring = substring.lower()
        stmt = stmt.filter(or_(
            func.lower(Exercise.name).contains(substring),
            func.lower(Exercise.description).contains(substring)
        ))

    result = await session.execute(stmt)
    exercises = result.scalars().all()

    return exercises



async def get_exercise_by_id(
    session: AsyncSession,
    exercise_id: int
) -> Exercise:
    """
    Возвращает упражнение по id
    """
    result = await session.execute(
        select(Exercise)
        .where(Exercise.id == exercise_id)
    )
    return result.scalar()



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
    exercise_order: int,
    set_data: SetData
) -> None:
    """
    Обновляет данные о подходе
    """
    set_id = set_data.get('id')
    result = await session.execute(
        update(Set)
        .values(
            weight = set_data.get('weight'),
            repetitions = set_data.get('repetitions'),
            overall_order = set_data.get('set_number'),
            exercise_order = exercise_order,
        )
        .where(
            Set.id == set_id,
            or_(
                Set.weight != set_data.get('weight'),
                Set.repetitions != set_data.get('repetitions'),
                Set.overall_order != set_data.get('set_number'),
                Set.exercise_order != exercise_order
            )
        )
    )
    return result.rowcount > 0



async def delete_old_sets(
    session: AsyncSession,
    training_id: int,
    current_sets_id: List[int]
) -> None:
    """
    Удаляет старые данные о подходах
    """
    result = await session.execute(
        delete(Set)
        .where(and_(
            Set.training_id == training_id,
            Set.id.not_in(current_sets_id)
        ))
        .returning(Set.id)
    )
    return sum(1 for _ in result.scalars()) > 0


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
    result = await session.execute(
        update(Training)
        .values(
            date = training_data.get('date').replace(tzinfo=None),
            comment = training_data.get('comment'),
        )
        .where(
            Training.id == training_id,
            or_(
                Training.date.cast(Date) != training_data.get('date').date(),
                Training.comment != training_data.get('comment')
            )
        )
    )
    return result.rowcount > 0


async def save_training_data(
    session: AsyncSession,
    training_data: TrainingData
) -> tuple[int, bool]:
    """
    Сохраняет данные о тренировке в базу данных    
    """
    update_flag = False
    create_flag = False

    training_id = training_data.get('id')
    if training_id is None:
        training_id = await save_new_training_data(session, training_data)
        create_flag = True
    else:
        is_updated = await update_training_data(session, training_data)
        update_flag = is_updated if is_updated else update_flag

    sets_id = []
    exercises = training_data.get('exercises')
    for exercise_id, exercise_data in exercises.items():
        sets = exercise_data['sets']
        
        for local_number, set_data in sets.items():
            set_id = set_data.get('id')
            if set_id is None:
                set_id = await save_new_set_data(session, training_id, exercise_id, local_number, set_data)
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
        
        training_data['exercises'][exercise_id]['sets'][exercise_order] = {
            'id': set_id,
            'set_number': overall_order,
            'weight': weight,
            'repetitions': repetitions,
            'time': execution_time
        }
    else:
        training_data['global_set_counter'] = overall_order

    for exercise in training_data['exercises'].values():
        exercise['local_set_counter'] = max(exercise['sets'].keys())

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