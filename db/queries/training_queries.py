from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List, Dict, Union, Tuple
from collections import namedtuple

from ..models import Set, Exercise, Training



async def get_most_frequent_exercises() -> List[Dict[str, Union[str, int]]]:
    exercises = [
        {1: 'Приседания'},
        {2: 'Отжимания'},
        {3: 'Планка'},
        {4: 'Выпады'},
        {5: 'Кранчи'},
        {6: 'Отжимания на брусьях'},
        {7: 'Подтягивания'},
        {8: 'Пресс'},
        {9: 'Приседания с гантелями'},
        {10: 'Французский жим'},
        {11: 'Жим ногами'},
        {12: 'Разгибание ног'},
        {13: 'Тяга верхнего блока'},
        # {14: 'Становая тяга'},
        # {15: 'Махи ногой'}
    ]
    return exercises




ExerciseSetCount = namedtuple('ExerciseSetCount', ['id', 'name', 'count'])



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