from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext

from typing import Dict, Union
from datetime import datetime

from .training_types import TrainingStates, TrainingMode
from utils.format_exercise_data import get_formatted_state_date
from keyboards.training_kb import (
    get_ikb_training_menu,
    DialogCalendar,
    DialogCalendarCallback,
    get_ikb_select_date,
)



router = Router()



@router.callback_query(
    F.data == 'today',
    TrainingStates.select_date
)
async def selected_date_today(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Инлайн кнопка "Сегодня"
    """
    await state.set_state(TrainingStates.menu)
    await state.update_data(mode=None)
    await state.update_data(date=datetime.now())

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    exercises = user_data.get('exercise_data')['exercises']

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_training_menu(
            is_add_edit_button = len(exercises) != 0,
            is_add_add_set_button = user_data.get("exercise_id") is not None
        ),
    )



@router.callback_query(
    F.data == 'other_date',
    TrainingStates.select_date
)
async def selected_date_other(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Инлайн кнопка "Другая дата"
    """
    await callback.message.edit_reply_markup(
        reply_markup=await DialogCalendar().start_calendar()
    )



@router.callback_query(
    DialogCalendarCallback.filter()
)
async def process_dialog_calendar(
    callback: CallbackQuery,
    callback_data: CallbackData,
    state: FSMContext
) -> None:
    """
    Обработка выбора даты в инлайн календаре
    """
    selected, date = await DialogCalendar().process_selection(callback, callback_data)

    if selected:
        await state.set_state(TrainingStates.menu)
        await state.update_data(mode=None)
        await state.update_data(date=date)

        user_data: Dict[str, Union[int, Dict]] = await state.get_data()
        exercises = user_data.get('exercise_data')['exercises']

        await callback.message.edit_text(
            text=await get_formatted_state_date(state),
            reply_markup = get_ikb_training_menu(
                is_add_edit_button = len(exercises) != 0,
                is_add_add_set_button = user_data.get("exercise_id") is not None
            ),
        )



@router.callback_query(
    F.data == 'to_date_menu',
    TrainingStates.select_date
)
async def back_to_date_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Инлайн кнопка "Меню даты" возврат в меню
    """
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(is_back_to_menu=user_data.get('date') is not None),
    )



@router.callback_query(
    F.data == 'edit_date',
    TrainingStates.edit_menu
)
async def open_edit_date(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Редактировать дату"
    """
    await state.set_state(TrainingStates.select_date)

    await state.update_data(mode=TrainingMode.EDIT_DATE)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(is_back_to_menu=True),
    )