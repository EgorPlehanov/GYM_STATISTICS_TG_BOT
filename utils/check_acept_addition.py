from aiogram.fsm.context import FSMContext

from typing import Dict, Union

from handlers.training_units import TrainingMode



async def check_acept_addition(state: FSMContext) -> bool:
    """
    Проверяет состояние можно ли добавлять подход
    """
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    is_exercise = user_data.get("cur_exercise_id") is not None
    is_weight = user_data.get("weight") is not None
    is_repetitions = user_data.get("repetitions") is not None
    
    match user_data.get('mode'):
        case TrainingMode.ADD_EXERCISE:
            return is_exercise and is_weight and is_repetitions
        case TrainingMode.ADD_SET:
            return is_weight and is_repetitions
        case TrainingMode.EDIT_SET:
            edit_exercise_id = user_data.get("edit_exercise_id")
            edit_set_id = user_data.get("edit_set_id")

            exercise = user_data.get("exercise_data", {}).get("exercises", {}).get(edit_exercise_id, {})
            set_data = exercise.get("sets", {}).get(edit_set_id, {})

            cur_weight = set_data.get("weight")
            cur_repetitions = set_data.get("repetitions")

            new_weight = user_data.get("weight")
            new_repetitions = user_data.get("repetitions")

            return (
                (is_weight and is_repetitions)
                and (cur_weight != new_weight or cur_repetitions != new_repetitions)
            )
        case _:
            return False
    