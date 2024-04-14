from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from typing import Dict, Union

from .training_types import TrainingStates
from utils.format_exercise_data import get_formatted_state_date
from utils.edit_exercise_data import (
    update_set,
    delete_all_exercises,
    delete_all_exercise_sets,
    delete_set,
)
from keyboards.training_kb import (
    get_ikb_edit_menu,
    ikb_edit_acept_delete,
)



router = Router()



@router.callback_query(F.data == 'to_edit_menu', TrainingStates.menu)
@router.callback_query(F.data == 'to_edit_menu', TrainingStates.select_date)
@router.callback_query(F.data == 'to_edit_menu', TrainingStates.edit_select_exercise)
async def open_edit_menu(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Редактировать тренировку"
    """
    await state.set_state(TrainingStates.edit_menu)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_menu(
            has_edit_exercise_button = len(user_data['exercise_data']['exercises']) > 0
        ),
    )



@router.callback_query(F.data == 'acept_edit', TrainingStates.select_weight)
@router.callback_query(F.data == 'acept_edit', TrainingStates.select_repetitions)
@router.callback_query(F.data == 'acept_edit', TrainingStates.acept_addition)
async def acept_edit(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Подтвердить изменения"
    """
    await state.set_state(TrainingStates.edit_menu)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    exercise_data = user_data.get('exercise_data')
    edit_exercise_id = user_data.get('edit_exercise_id')
    edit_set_id = user_data.get('edit_set_id')
    new_weight = user_data.get('weight')
    new_repetitions = user_data.get('repetitions')

    is_updated = update_set(exercise_data, edit_exercise_id, edit_set_id, new_weight, new_repetitions)

    await state.update_data(mode=None)
    await state.update_data(edit_exercise_id=None)
    await state.update_data(edit_exercise_name=None)
    await state.update_data(edit_set_id=None)
    await state.update_data(edit_set_number=None)
    await state.update_data(weight=None)
    await state.update_data(repetitions=None)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_menu(
            has_edit_exercise_button = len(exercise_data['exercises']) > 0
        )
    )



@router.callback_query(F.data == 'delete_all_exercises', TrainingStates.edit_select_exercise)
@router.callback_query(F.data == 'delete_all_sets', TrainingStates.edit_select_set)
@router.callback_query(F.data == 'delete_set', TrainingStates.select_weight)
@router.callback_query(F.data == 'delete_set', TrainingStates.select_repetitions)
async def delete_acept(callback: CallbackQuery, state: FSMContext):
    """
    Подтвержнение удаления
    """
    state_before_delete = await state.get_state()

    await state.update_data(state_before_delete=state_before_delete)
    await state.update_data(reply_markup_before_delete=callback.message.reply_markup)

    await state.set_state(TrainingStates.edit_delete)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=ikb_edit_acept_delete,
    )



@router.callback_query(F.data == 'delete_cancel', TrainingStates.edit_delete)
async def delete_cancel(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Отмена удаления"
    """
    user_data = await state.get_data()
    state_before_delete = user_data.get('state_before_delete')
    reply_markup_before_delete = user_data.get('reply_markup_before_delete')

    await state.set_state(state_before_delete)
    
    await state.update_data(state_before_delete=None)
    await state.update_data(reply_markup_before_delete=None)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=reply_markup_before_delete
    )



@router.callback_query(F.data == 'delete_acepted', TrainingStates.edit_delete)
async def delete_exercises_sets(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Удалить упражнения/подходы/подход"
    """
    await state.set_state(TrainingStates.edit_menu)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    edit_exercise_id = user_data.get('edit_exercise_id')
    edit_set_id = user_data.get('edit_set_id')

    if edit_exercise_id is None:
        delete_all_exercises(user_data['exercise_data'])
    elif edit_set_id is None:
        delete_all_exercise_sets(user_data['exercise_data'], edit_exercise_id)
    else:
        delete_set(user_data['exercise_data'], edit_exercise_id, edit_set_id)

    exercise_data = user_data.get('exercise_data')
    cur_exercise_id = exercise_data.get('cur_exercise_id')
    if cur_exercise_id not in exercise_data['exercises']:
        await state.update_data(exercise_id=None)
        await state.update_data(exercise_name=None)
        await state.update_data(last_weight=None)
        await state.update_data(last_repetitions=None)

    await state.update_data(state_before_delete=None)
    await state.update_data(reply_markup_before_delete=None)
    await state.update_data(mode=None)
    await state.update_data(edit_exercise_id=None)
    await state.update_data(edit_exercise_name=None)
    await state.update_data(edit_set_id=None)
    await state.update_data(edit_set_number=None)
    await state.update_data(weight=None)
    await state.update_data(repetitions=None)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_menu(
            has_edit_exercise_button = len(user_data['exercise_data']['exercises']) > 0
        ),
    )
    