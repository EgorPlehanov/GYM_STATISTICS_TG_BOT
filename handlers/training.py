from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackQuery

from typing import Dict, Union

from .training_types import TrainingStates
from utils.edit_exercise_data import initialize_exercise_data
from utils.format_exercise_data import get_formatted_state_date
from keyboards import (
    get_ikb_select_date,
    get_ikb_training_menu,
)
from db.db import get_most_frequent_exercises
from handlers import (
    training_acept,
    training_select_date,
    training_select_exercise,
    training_select_weight,
    training_select_repetitions,
    training_finish_add_comment,
    training_edit_menu,
    training_edit_select_exercise,
    training_edit_select_set,
)



router = Router()
router.include_routers(
    training_select_date.router,
    training_select_exercise.router,
    training_select_weight.router,
    training_select_repetitions.router,
    training_acept.router,
    training_finish_add_comment.router,
    training_edit_menu.router,
    training_edit_select_exercise.router,
    training_edit_select_set.router,
)



@router.message(StateFilter(None), Command("training"))
async def cmd_training(message: Message, state: FSMContext) -> None:
    """
    Команда /training
    """
    await state.set_state(TrainingStates.select_date)

    await state.update_data(exercise_data=initialize_exercise_data())
    await state.update_data(most_frequent_exercises=await get_most_frequent_exercises())

    answer = await message.answer(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(is_back_to_menu=False),
    )
    await state.update_data(message_id=answer.message_id)



@router.callback_query(F.data == 'to_menu', TrainingStates.select_date)
@router.callback_query(F.data == 'to_menu', TrainingStates.select_exercise)
@router.callback_query(F.data == 'to_menu', TrainingStates.select_weight)
@router.callback_query(F.data == 'to_menu', TrainingStates.add_comment)
@router.callback_query(F.data == 'to_menu', TrainingStates.edit_menu)
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Назад" возврат в меню
    """
    await state.set_state(TrainingStates.menu)

    await state.update_data(mode=None)
    await state.update_data(cur_exercise_id=None)
    await state.update_data(cur_exercise_name=None)
    await state.update_data(weight=None)
    await state.update_data(repetitions=None)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    exercises = user_data.get('exercise_data')['exercises']

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_training_menu(
            is_add_edit_button = len(exercises) != 0,
            is_add_add_set_button = user_data.get("exercise_id") is not None
        ),
    )



@router.callback_query(F.data == 'cancel', TrainingStates.select_date)
@router.callback_query(F.data == 'cancel', TrainingStates.menu)
async def cancel_trainings(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "❌"("Отмена")
    """
    await state.clear()
    await callback.message.delete()

    await callback.message.answer("Слабак🫵, попробуй ещё раз 🤣")
