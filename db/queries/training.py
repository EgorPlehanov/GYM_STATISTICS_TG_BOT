from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List, Dict, Union
from datetime import datetime

from ..models import Exercise, Set, Training



async def get_sorted_exercises_by_sets_count(
    session: AsyncSession,
    user_id: int,
    page_size: int = 5,
    page_num: int = 0
) -> List[Exercise]:
    """

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


async def save_training_data(
    session: AsyncSession,
    user_id: int,
    date: datetime,
    comment: str,
    training_data: TrainingData
) -> None:
    """
    Сохраняет данные о тренировке в базу данных    
    """
    training = Training(
        user_id=user_id,
        date=date.replace(tzinfo=None),
        comment=comment,
    )
    session.add(training)
    await session.flush()  # для получения training.id
    
    exercises = training_data['exercises']
    for exercise_id, exercise_data in exercises.items():
        sets = exercise_data['sets']
        
        for set_id, set_data in sets.items():
            set_number = set_data['set_number']
            weight = set_data['weight']
            repetitions = set_data['repetitions']
            execution_time = set_data['time'].replace(tzinfo=None)
            
            new_set = Set(
                training_id=training.id,
                exercise_id=exercise_id,
                overall_order=set_number,
                exercise_order=set_id,
                weight=weight,
                repetitions=repetitions,
                execution_time=execution_time
            )
            session.add(new_set)
    
    await session.commit()



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
) -> dict:
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

    sets_result = await session.execute(
        select(
            Set.exercise_id.label('exercise_id'),
            Exercise.name.label('exercise_name'),
            Set.overall_order.label('overall_order'),
            Set.exercise_order.label('exercise_order'),
            Set.weight.label('weight'),
            Set.repetitions.label('repetitions'),
            Set.execution_time.label('execution_time')
        )
        .join(Training, Training.id == Set.training_id)
        .join(Exercise, Exercise.id == Set.exercise_id)
        .filter(Training.user_id == user_id, Training.date == date)
    )
    
    training_data = {
        'id': training_result.first()['id'],
        'date': date,
        'comment': training_result.first()['comment'],
        'global_set_counter': 0,
        'exercises': {}
    }
    
    for row in sets_result:
        exercise_id, exercise_name, overall_order, exercise_order, weight, repetitions, execution_time = row
        
        if exercise_id not in training_data['exercises']:
            training_data['exercises'][exercise_id] = {'exercise_name': exercise_name, 'local_set_counter': 0, 'sets': {}}
        
        training_data['exercises'][exercise_id]['local_set_counter'] += 1
        training_data['global_set_counter'] += 1
        
        training_data['exercises'][exercise_id]['sets'][overall_order] = {
            'set_number': exercise_order,
            'weight': weight,
            'repetitions': repetitions,
            'time': execution_time
        }

    return training_data