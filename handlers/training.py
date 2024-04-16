from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackQuery

from typing import Dict, Union
from sqlalchemy.ext.asyncio import AsyncSession

from .training_units import (
    TrainingStates,
    select_date_router,
    select_exercise_router,
    select_weight_router,
    select_repetitions_router,
    select_sets_count_router,
    acept_router,
    edit_menu_router,
    edit_select_exercise_router,
    edit_select_set_router,
    finish_add_comment_router,
)
from utils.format_exercise_data import get_formatted_state_date
from keyboards.training_kb import (
    get_ikb_select_date,
    get_ikb_training_menu,
)
from middlewares import (
    DBSessionMiddleware,
    ChatActionMiddleware,
)
from db.database import async_session_factory
from db.queries import get_sorted_exercises_by_sets_count



router = Router()
router.message.filter(F.chat.type == "private")
router.message.middleware(DBSessionMiddleware(async_session_factory))
router.message.middleware(ChatActionMiddleware())
router.include_routers(
    select_date_router,
    select_exercise_router,
    select_weight_router,
    select_repetitions_router,
    select_sets_count_router,
    acept_router,
    edit_menu_router,
    edit_select_exercise_router,
    edit_select_set_router,
    finish_add_comment_router,
)



@router.message(StateFilter(None), Command("training"))
async def cmd_training(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """
    Команда /training
    """
    await state.set_state(TrainingStates.select_date)

    await state.update_data(most_frequent_exercises=await get_sorted_exercises_by_sets_count(
        session = session,
        user_id=message.from_user.id,
        page_size=15
    ))

    answer = await message.answer(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(is_back_to_menu=False),
    )
    await state.update_data(message_id=answer.message_id)



@router.callback_query(F.data == 'to_menu', TrainingStates.select_date)
@router.callback_query(F.data == 'to_menu', TrainingStates.select_exercise)
@router.callback_query(F.data == 'to_menu', TrainingStates.select_weight)
@router.callback_query(F.data == 'to_menu', TrainingStates.acept_addition)
@router.callback_query(F.data == 'to_menu', TrainingStates.edit_menu)
@router.callback_query(F.data == 'to_menu', TrainingStates.add_comment)
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
    await state.update_data(sets_count=None)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    exercises = user_data.get('exercise_data')['exercises']

    last_weight = str(user_data.get('last_weight', '')).rstrip('0').rstrip(".")
    last_repetitions = user_data.get('last_repetitions', '')

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_training_menu(
            is_add_edit_button = len(exercises) != 0,
            is_add_add_set_button = user_data.get("exercise_id") is not None,
            repeat_set_button_text = f"{last_weight}x{last_repetitions}"
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
