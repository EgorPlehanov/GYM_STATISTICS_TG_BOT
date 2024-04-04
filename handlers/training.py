from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackQuery

from typing import Dict, Union

from .training_states import TrainingStates
from utils.edit_exercise_data import initialize_exercise_data
from utils.format_exercise_data import get_formatted_state_date
from keyboards import (
    get_ikb_select_date,
    get_ikb_training_menu,
)
from db.db import get_most_frequent_exercises
from handlers import (
    training_select_date,
    training_select_exercise,
    training_select_weight,
    training_select_repetitions,
    training_acept_addition,
)



router = Router()
router.include_routers(
    training_select_date.router,
    training_select_exercise.router,
    training_select_weight.router,
    training_select_repetitions.router,
    training_acept_addition.router,
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
        reply_markup = get_ikb_training_menu(len(exercises) != 0),
    )



@router.callback_query(F.data == 'cancel', TrainingStates.select_date)
@router.callback_query(F.data == 'cancel', TrainingStates.menu)
async def cancel_trainings(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "❌"("Отмена")
    """
    await state.clear()
    await callback.message.delete()










# @router.callback_query(F.data == 'edit_menu', TrainingStates.finish)
# async def edit_sets_handler(callback: CallbackQuery, state: FSMContext):
#     """
#     Инлайн кнопка "Внести исправления"
#     """
#     await state.set_state(TrainingStates.edit_choose_exercise)
    
#     user_data: Dict[str, Union[int, Dict]] = await state.get_data()
#     exercises = user_data.get('exercise_data').get('exercises')

#     await callback.message.edit_text(
#         text=await get_formatted_state_date(state),
#         reply_markup = get_ikb_edit_select_exercise_fab(exercises)
#     )


# @router.callback_query(
#     EditTrainingExercisePagination.filter(F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])),
#     TrainingStates.edit_choose_exercise
# )
# async def selected_exercise_pagination(
#     callback: CallbackQuery,
#     callback_data: TrainingExercisePagination,
#     state: FSMContext
# ):
#     """
#     Пагинация выбора упражнения
#     """
#     page = int(callback_data.page)
#     user_data: Dict[str, Union[int, Dict]] = await state.get_data()
#     exercises = user_data.get('exercise_data').get('exercises')

#     if callback_data.action == PaginationAction.PREV:
#         page = page - 1 if page > 0 else 0
#     elif callback_data.action == PaginationAction.NEXT:
#         page = page + 1 if page < len(exercises) - 1 else page

#     await callback.message.edit_reply_markup(
#         reply_markup = get_ikb_edit_select_exercise_fab(exercises, page),
#     )



# @router.callback_query(F.data == 'select_exercise_back', TrainingStates.select_exercise)
# @router.callback_query(F.data == 'select_back', TrainingStates.select_additional_weight)
# @router.callback_query(F.data == 'select_back', TrainingStates.select_repetitions)
# @router.callback_query(F.data == 'edit_menu_back', TrainingStates.edit_choose_exercise)
# @router.callback_query(F.data == 'edit_menu_back', TrainingStates.edit_choose_set)
# @router.callback_query(F.data == 'edit_menu_back', TrainingStates.edit_choose_mode)
# async def edit_back_finish(callback: CallbackQuery, state: FSMContext):
#     """
#     Инлайн кнопка "Назад" в режиме изменения
#     """
#     back_state = {
#         "TrainingStates:select_exercise": "TrainingStates:finish",
#         "TrainingStates:select_additional_weight": "TrainingStates:select_exercise",
#         "TrainingStates:select_repetitions": "TrainingStates:select_additional_weight",
#         "TrainingStates:edit_choose_exercise": "TrainingStates:finish",
#         "TrainingStates:edit_choose_set": "TrainingStates:edit_choose_exercise",
#         "TrainingStates:edit_choose_mode": "TrainingStates:edit_choose_set",
#     }
#     current_state = await state.get_state()
#     new_state = back_state[current_state]
#     await state.set_state(new_state)

#     ikb_by_state = {
#         "TrainingStates:finish": ikb_finish_training,
#         "TrainingStates:select_exercise": get_ikb_select_exercise_fab,
#         "TrainingStates:select_additional_weight": get_ikb_open_inline_search,
#         "TrainingStates:edit_choose_exercise": get_ikb_edit_select_exercise_fab,
#         # "TrainingStates:edit_choose_set": get_ikb_edit_choose_set_fab,
#     }
#     new_reply_markup = ikb_by_state[new_state]

#     await callback.message.edit_text(
#         text=await get_formatted_state_date(state),
#         reply_markup=new_reply_markup() if isinstance(new_reply_markup, Callable) else new_reply_markup
#     )


# @router.callback_query(
#     F.data == 'finish_training',
#     TrainingStates.finish
# )
# async def finish_training(callback: CallbackQuery, state: FSMContext):
#     """
#     Инлайн кнопка "Завершить тренировку"
#     """
#     await state.clear()
#     await callback.message.delete()