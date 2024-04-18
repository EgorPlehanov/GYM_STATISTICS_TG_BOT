from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from typing import Dict, Union
from datetime import datetime

from .training_types import TrainingStates
from utils.edit_exercise_data import add_exercise, add_set, update_set
from utils.format_training_data import get_formatted_state_date
from keyboards.training_kb import get_ikb_training_menu



router = Router()



@router.callback_query(F.data == 'acept_addition', TrainingStates.select_exercise)
@router.callback_query(F.data == 'acept_addition', TrainingStates.select_weight)
@router.callback_query(F.data == 'acept_addition', TrainingStates.select_repetitions)
@router.callback_query(F.data == 'acept_addition', TrainingStates.select_sets_count)
@router.callback_query(F.data == 'acept_addition', TrainingStates.acept_addition)
async def acept_addition(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Подтвердить" добавляет упражнение/подход
    """
    await state.set_state(TrainingStates.menu)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    exercise_data = user_data.get('exercise_data')
    exercise_id = user_data.get('cur_exercise_id')
    exercise_name = user_data.get('cur_exercise_name')
    weight = user_data.get('weight')
    repetitions = user_data.get('repetitions')
    sets_count = user_data.get('sets_count')
    time = callback.message.date
    
    add_exercise(exercise_data, exercise_id, exercise_name)
    for _ in range(sets_count):
        add_set(exercise_data, exercise_id, weight, repetitions, time)

    await state.update_data(exercise_id=exercise_id)
    await state.update_data(exercise_name=exercise_name)

    await state.update_data(mode=None)
    await state.update_data(cur_exercise_id=None)
    await state.update_data(cur_exercise_name=None)
    await state.update_data(weight=None)
    await state.update_data(repetitions=None)
    await state.update_data(sets_count=None)
    await state.update_data(last_weight=weight)
    await state.update_data(last_repetitions=repetitions)
    
    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_training_menu(
            is_add_add_set_button=True,
            repeat_set_button_text=f"{str(weight).rstrip('0').rstrip('.')}×{repetitions}",
        )
    )