from aiogram.fsm.context import FSMContext

from typing import Dict, Union



async def check_acept_addition(state: FSMContext) -> bool:
    """
    Проверяет состояние FSM
    """
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    is_exercise = user_data.get("cur_exercise_id") is not None
    is_weight = user_data.get("weight") is not None
    is_repetitions = user_data.get("repetitions") is not None
    
    match user_data.get('mode'):
        case 'add_exercise':
            return is_exercise and is_weight and is_repetitions
        case 'add_set':
            return is_weight and is_repetitions
        case _:
            return False
    