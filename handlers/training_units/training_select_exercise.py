from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineQuery,
    InlineQueryResultArticle, InputTextMessageContent
)
from aiogram.fsm.context import FSMContext

from typing import Dict, Union, List
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet

from .training_types import (
    TrainingStates,
    TrainingMode,
    exercise_button_by_mode,
    Button
)
from keyboards.keyboards_types import PaginationAction
from keyboards.training_kb import (
    get_ikb_select_exercise_fab,
    TrainingExercisePagination,
    get_ikb_open_inline_search,
)
from utils.format_exercise_data import get_formatted_state_date
from utils.check_acept_addition import check_acept_addition
from utils.weight_repetitions_modes import get_weight_repetitions_modes_values
from middlewares import DBSessionMiddleware
from db.database import async_session_factory
from db.models import Exercise
from db.queries import (
    get_sorted_exercises_by_sets_count,
    get_exercise_by_id
)



router = Router()
router.inline_query.middleware(DBSessionMiddleware(async_session_factory))



# Генерация ключа для шифрования
key = Fernet.generate_key()
cipher = Fernet(key)



@router.callback_query(
    F.data == 'add_exercise',
    TrainingStates.menu
)
async def add_exercise_handler(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Добавить упражнение"
    """
    await state.set_state(TrainingStates.select_exercise)
    await state.update_data(mode=TrainingMode.ADD_EXERCISE)
    await state.update_data(sets_count=1)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises = user_data.get('most_frequent_exercises', [])

    selected_exercise_id = user_data.get("cur_exercise_id") or user_data.get("exercise_id")

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_select_exercise_fab(
            exercise_data=most_frequent_exercises,
            selected_exercise_id=selected_exercise_id
        ),
    )



@router.callback_query(
    TrainingExercisePagination.filter(F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])),
    TrainingStates.select_exercise
)
async def selected_exercise_pagination(
    callback: CallbackQuery,
    callback_data: TrainingExercisePagination,
    state: FSMContext
):
    """
    Пагинация выбора упражнения
    """
    page = int(callback_data.page)
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises = user_data.get('most_frequent_exercises', [])

    if callback_data.action == PaginationAction.PREV:
        page = page - 1 if page > 0 else 0
    elif callback_data.action == PaginationAction.NEXT:
        page = page + 1 if page < len(most_frequent_exercises) - 1 else page

    selected_exercise_id = user_data.get("cur_exercise_id") or user_data.get("exercise_id")

    await callback.message.edit_reply_markup(
        reply_markup = get_ikb_select_exercise_fab(
            exercise_data=most_frequent_exercises,
            page=page,
            has_acept_addition_button = await check_acept_addition(state),
            selected_exercise_id=selected_exercise_id
        ),
    )



@router.callback_query(
    TrainingExercisePagination.filter(F.action == PaginationAction.SET),
    TrainingStates.select_exercise
)
async def selected_exercise( 
    callback: CallbackQuery,
    callback_data: TrainingExercisePagination,
    state: FSMContext
):
    """
    Кнопка выбора упражнения
    """
    await state.set_state(TrainingStates.select_weight)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises: List[Exercise] = user_data.get('most_frequent_exercises', [])

    exercise_id = int(callback_data.exercise_id)
    exercise = next(e for e in most_frequent_exercises if e.id == exercise_id)

    # Перемещаем выбранное упражнение в начало списка
    most_frequent_exercises.remove(exercise)
    most_frequent_exercises.insert(0, exercise)

    await state.update_data(cur_exercise_name=exercise.name)
    await state.update_data(cur_exercise_id=exercise_id)

    back_button: Button = exercise_button_by_mode.get(user_data.get('mode'))

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            back_button_text = back_button.text,
            back_button_callback_data = back_button.callback_data,
            has_next_button = user_data.get("weight") is not None,
            next_button_text = "Повторения",
            next_button_callback_data = "to_repetitions",
            has_delete_set_button = user_data.get("mode") == TrainingMode.EDIT_SET,
            switch_inline_query = get_weight_repetitions_modes_values(
                user_data = await state.get_data(),
                is_weight = True
            )
        ),
    )



@router.callback_query(F.data == "to_exercise", TrainingStates.select_weight)
@router.callback_query(F.data == "to_exercise", TrainingStates.acept_addition)
async def back_to_exercise(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Назад" возврат к выбору упражнения
    """
    await state.set_state(TrainingStates.select_exercise)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises = user_data.get('most_frequent_exercises', [])

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_select_exercise_fab(
            exercise_data = most_frequent_exercises,
            has_next_button = user_data.get("cur_exercise_id") is not None,
            has_acept_addition_button = await check_acept_addition(state),
            selected_exercise_id=user_data.get("cur_exercise_id")
        ),
    )



@router.inline_query(TrainingStates.select_exercise)
async def inline_exercise(inline_query: InlineQuery, state: FSMContext, session: AsyncSession):
    """
    Инлайн выбор упражнения: возвращает список значений
    """
    offset = int(inline_query.offset) if inline_query.offset else 0
    page_size = 50

    exercises: List[Exercise] = await get_sorted_exercises_by_sets_count(
        session = session,
        user_id=inline_query.from_user.id,
        page_size=page_size,
        page_num=offset//page_size,
        substring=inline_query.query
    )

    results = []
    for exercise in exercises:
        results.append(
            InlineQueryResultArticle(
                id = str(exercise.id),
                title = exercise.name,
                description = exercise.description,
                input_message_content=InputTextMessageContent(
                    message_text = cipher.encrypt(str(exercise.id).encode())
                ),
            )
        )
    if len(results) < 50:
        await inline_query.answer(
            results,
            cache_time = 0,
            is_personal = True
        )
    else:
        await inline_query.answer(
            results,
            next_offset = str(offset+50),
            cache_time = 0,
            is_personal = True
        )



@router.message(F.via_bot, TrainingStates.select_exercise)
async def inline_selected_exercise(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Инлайн упражнение: обработка выбранного значения
    """
    await message.delete()

    await state.set_state(TrainingStates.select_weight)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises: List[Exercise] = user_data.get('most_frequent_exercises', [])

    exercise_id = int(cipher.decrypt(message.text).decode())
    exercise = await get_exercise_by_id(session=session, exercise_id=exercise_id)

    # Перемещаем выбранное упражнение в начало списка
    index_to_remove = next((i for i, e in enumerate(most_frequent_exercises) if e.id == exercise.id), None)
    if index_to_remove is not None:
        most_frequent_exercises.pop(index_to_remove)
    most_frequent_exercises.insert(0, exercise)

    await state.update_data(cur_exercise_name=exercise.name)
    await state.update_data(cur_exercise_id=exercise_id)

    back_button: Button = exercise_button_by_mode.get(user_data.get('mode'))

    await message.bot.edit_message_text(
        chat_id = message.chat.id,
        message_id = user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            back_button_text = back_button.text,
            back_button_callback_data = back_button.callback_data,
            has_next_button = user_data.get("weight") is not None,
            next_button_text = "Повторения",
            next_button_callback_data = "to_repetitions",
            has_delete_set_button = user_data.get("mode") == TrainingMode.EDIT_SET,
            switch_inline_query = get_weight_repetitions_modes_values(
                user_data = await state.get_data(),
                is_weight = True
            )
        ),
    )