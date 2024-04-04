from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext

from typing import Dict, Union
from datetime import datetime

from .training_states import TrainingStates
from utils.format_exercise_data import get_formatted_state_date
from keyboards import (
    get_ikb_training_menu,
    DialogCalendar,
    DialogCalendarCallback,
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
    await state.update_data(date=datetime.now())

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    exercises = user_data.get('exercise_data')['exercises']

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_training_menu(len(exercises) != 0),
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
        await state.update_data(date=date)

        user_data: Dict[str, Union[int, Dict]] = await state.get_data()
        exercises = user_data.get('exercise_data')['exercises']

        await callback.message.edit_text(
            text=await get_formatted_state_date(state),
            reply_markup = get_ikb_training_menu(len(exercises) != 0),
        )