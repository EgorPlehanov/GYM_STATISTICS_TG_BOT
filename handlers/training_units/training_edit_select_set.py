from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from typing import Dict, Union

from .training_types import (
    TrainingStates,
    TrainingMode,
    acept_button_by_mode,
)
from utils.format_training_data import get_formatted_state_date
from utils.weight_repetitions_modes import get_weight_repetitions_modes_values
from keyboards.keyboards_types import PaginationAction
from keyboards.training_kb import (
    EditTrainingSetPagination,
    get_ikb_edit_select_set_fab,
    get_ikb_open_inline_search,
)
from utils.check_acept_addition import check_acept_addition



router = Router()



@router.callback_query(
    EditTrainingSetPagination.filter(
        F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])
    ),
    TrainingStates.edit_select_set
)
async def selected_set_pagination(
    callback: CallbackQuery,
    callback_data: EditTrainingSetPagination,
    state: FSMContext
):
    """
    Пагинация выбора упражнения
    """
    page = int(callback_data.page)
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    edit_exercise_id = user_data['edit_exercise_id']
    exercise_sets = user_data['exercise_data']['exercises'][edit_exercise_id]['sets']

    if callback_data.action == PaginationAction.PREV:
        page = page - 1 if page > 0 else 0
    elif callback_data.action == PaginationAction.NEXT:
        page = page + 1 if page < len(exercise_sets) - 1 else page

    await callback.message.edit_reply_markup(
        reply_markup = get_ikb_edit_select_set_fab(exercise_sets, page),
    )


    
@router.callback_query(
    EditTrainingSetPagination.filter(F.action == PaginationAction.SET),
    TrainingStates.edit_select_set
)
async def selected_set(
    callback: CallbackQuery,
    callback_data: EditTrainingSetPagination,
    state: FSMContext
):
    """
    Выбран подход упражнения из меню редактирования
    """
    await state.set_state(TrainingStates.select_weight)

    set_id = callback_data.set_id

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    edit_exercise_id = user_data['edit_exercise_id']
    sets = user_data['exercise_data']['exercises'][edit_exercise_id]['sets']
    set_data: Dict[str, Union[int, float]] = sets.get(set_id, {})

    await state.update_data(edit_set_id=set_id)
    await state.update_data(edit_set_number=set_data.get('set_number'))
    await state.update_data(weight=set_data.get('weight'))
    await state.update_data(repetitions=set_data.get('repetitions'))

    await state.update_data(mode=TrainingMode.EDIT_SET)

    acept_button = acept_button_by_mode.get(TrainingMode.EDIT_SET)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            back_button_text = "Подход",
            back_button_callback_data = "to_edit_menu_set",
            has_next_button = True,
            next_button_text = "Повторения",
            next_button_callback_data = "to_repetitions",
            has_acept_button = await check_acept_addition(state),
            acept_button_text = acept_button.text,
            acept_button_callback_data = acept_button.callback_data,
            has_delete_set_button = True,
            switch_inline_query = get_weight_repetitions_modes_values(
                user_data = await state.get_data(),
                is_weight = True
            )
        ),
    )



@router.callback_query(
    F.data == "to_edit_menu_set",
    TrainingStates.select_weight,
)
async def back_to_edit_exercise(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Назад"
    """
    await state.set_state(TrainingStates.edit_select_set)

    await state.update_data(edit_set_id=None)
    await state.update_data(edit_set_number=None)
    await state.update_data(weight=None)
    await state.update_data(repetitions=None)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    edit_exercise_id = user_data['edit_exercise_id']
    exercise_sets = user_data['exercise_data']['exercises'][edit_exercise_id]['sets']

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_select_set_fab(exercise_sets),
    )