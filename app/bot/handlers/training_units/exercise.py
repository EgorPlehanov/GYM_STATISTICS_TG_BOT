from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)
from cryptography.fernet import Fernet

from app.bot.client import BotApiClient
from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    Button,
    TrainingMode,
    TrainingStates,
    check_accept_addition,
    exercise_button_by_mode,
    get_training_draft,
    get_weight_repetitions_modes_values_from_draft,
    set_training_draft,
)
from app.bot.keyboards.keyboards_types import PaginationAction
from app.bot.keyboards.training_kb import (
    TrainingExercisePagination,
    get_ikb_open_inline_search,
    get_ikb_select_exercise_fab,
)

router = Router()


# Временный payload для inline-выбора упражнения. Позже будет заменен на
# устойчивый signed/Redis-backed payload.
key = Fernet.generate_key()
cipher = Fernet(key)


@router.callback_query(F.data == "add_exercise", TrainingStates.menu)
async def add_exercise_handler(callback: CallbackQuery, state: FSMContext):
    """Открывает выбор упражнения для добавления в тренировку."""
    await state.set_state(TrainingStates.select_exercise)

    draft = await get_training_draft(state)
    draft.selection.mode = TrainingMode.ADD_EXERCISE.value
    draft.selection.sets_count = 1
    await set_training_draft(state, draft)

    most_frequent_exercises = draft.suggestions.most_frequent_exercises
    selected_exercise_id = draft.selection.exercise_id or draft.ui.current_exercise_id

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_exercise_fab(
            exercise_data=most_frequent_exercises, selected_exercise_id=selected_exercise_id
        ),
    )


@router.callback_query(
    TrainingExercisePagination.filter(F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])),
    TrainingStates.select_exercise,
)
async def selected_exercise_pagination(
    callback: CallbackQuery, callback_data: TrainingExercisePagination, state: FSMContext
):
    """Переключает страницу списка частых упражнений."""
    page = int(callback_data.page)
    draft = await get_training_draft(state)
    most_frequent_exercises = draft.suggestions.most_frequent_exercises

    if callback_data.action == PaginationAction.PREV:
        page = page - 1 if page > 0 else 0
    elif callback_data.action == PaginationAction.NEXT:
        page = page + 1 if page < len(most_frequent_exercises) - 1 else page

    selected_exercise_id = draft.selection.exercise_id or draft.ui.current_exercise_id

    await callback.message.edit_reply_markup(
        reply_markup=get_ikb_select_exercise_fab(
            exercise_data=most_frequent_exercises,
            page=page,
            has_accept_addition_button=await check_accept_addition(state),
            selected_exercise_id=selected_exercise_id,
        ),
    )


@router.callback_query(
    TrainingExercisePagination.filter(F.action == PaginationAction.SET),
    TrainingStates.select_exercise,
)
async def selected_exercise(
    callback: CallbackQuery, callback_data: TrainingExercisePagination, state: FSMContext
):
    """Сохраняет упражнение, выбранное из списка частых упражнений."""
    await state.set_state(TrainingStates.select_weight)

    draft = await get_training_draft(state)
    most_frequent_exercises = draft.suggestions.most_frequent_exercises

    exercise_id = int(callback_data.exercise_id)
    exercise = next(e for e in most_frequent_exercises if int(e["id"]) == exercise_id)

    # Перемещаем выбранное упражнение в начало списка
    most_frequent_exercises.remove(exercise)
    most_frequent_exercises.insert(0, exercise)

    draft.selection.exercise_id = exercise_id
    draft.selection.exercise_name = exercise["name"]
    draft.suggestions.most_frequent_exercises = most_frequent_exercises
    await set_training_draft(state, draft)

    mode = TrainingMode(draft.selection.mode)
    back_button: Button = exercise_button_by_mode.get(mode)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_open_inline_search(
            entity_name="вес",
            back_button_text=back_button.text,
            back_button_callback_data=back_button.callback_data,
            has_next_button=draft.selection.weight is not None,
            next_button_text="Повторения",
            next_button_callback_data="to_repetitions",
            has_delete_set_button=mode == TrainingMode.EDIT_SET,
            switch_inline_query=get_weight_repetitions_modes_values_from_draft(
                draft,
                is_weight=True,
            ),
        ),
    )


@router.callback_query(F.data == "to_exercise", TrainingStates.select_weight)
@router.callback_query(F.data == "to_exercise", TrainingStates.accept_addition)
async def back_to_exercise(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя к выбору упражнения."""
    await state.set_state(TrainingStates.select_exercise)

    draft = await get_training_draft(state)
    most_frequent_exercises = draft.suggestions.most_frequent_exercises

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_exercise_fab(
            exercise_data=most_frequent_exercises,
            has_next_button=draft.selection.exercise_id is not None,
            has_accept_addition_button=await check_accept_addition(state),
            selected_exercise_id=draft.selection.exercise_id,
        ),
    )


@router.inline_query(TrainingStates.select_exercise)
async def inline_exercise_search(inline_query: InlineQuery, state: FSMContext):
    """Возвращает inline-результаты поиска упражнений."""
    offset = int(inline_query.offset) if inline_query.offset else 0
    page_size = 50

    async with BotApiClient() as api_client:
        exercises = await api_client.get_exercises(
            telegram_id=inline_query.from_user.id,
            page_size=page_size,
            page_num=offset // page_size,
            substring=inline_query.query,
        )

    results = []
    for exercise in exercises:
        results.append(
            InlineQueryResultArticle(
                id=str(exercise.id),
                title=exercise.name,
                description=exercise.description,
                input_message_content=InputTextMessageContent(
                    message_text=cipher.encrypt(str(exercise.id).encode())
                ),
            )
        )
    if len(results) < 50:
        await inline_query.answer(results, cache_time=0, is_personal=True)
    else:
        await inline_query.answer(
            results, next_offset=str(offset + 50), cache_time=0, is_personal=True
        )


@router.message(F.via_bot, TrainingStates.select_exercise)
async def inline_selected_exercise(
    message: Message,
    state: FSMContext,
):
    """Сохраняет упражнение, выбранное через inline-поиск."""
    await message.delete()

    await state.set_state(TrainingStates.select_weight)

    draft = await get_training_draft(state)
    most_frequent_exercises = draft.suggestions.most_frequent_exercises

    exercise_id = int(cipher.decrypt(message.text).decode())
    async with BotApiClient() as api_client:
        exercise = await api_client.get_exercise(exercise_id=exercise_id)

    # Перемещаем выбранное упражнение в начало списка
    index_to_remove = next(
        (i for i, e in enumerate(most_frequent_exercises) if int(e["id"]) == exercise.id),
        None,
    )
    if index_to_remove is not None:
        most_frequent_exercises.pop(index_to_remove)
    most_frequent_exercises.insert(
        0,
        {
            "id": exercise.id,
            "name": exercise.name,
            "description": exercise.description,
        },
    )

    draft.selection.exercise_id = exercise_id
    draft.selection.exercise_name = exercise.name
    draft.suggestions.most_frequent_exercises = most_frequent_exercises
    await set_training_draft(state, draft)

    mode = TrainingMode(draft.selection.mode)
    back_button: Button = exercise_button_by_mode.get(mode)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=draft.ui.message_id,
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_open_inline_search(
            entity_name="вес",
            back_button_text=back_button.text,
            back_button_callback_data=back_button.callback_data,
            has_next_button=draft.selection.weight is not None,
            next_button_text="Повторения",
            next_button_callback_data="to_repetitions",
            has_delete_set_button=mode == TrainingMode.EDIT_SET,
            switch_inline_query=get_weight_repetitions_modes_values_from_draft(
                draft,
                is_weight=True,
            ),
        ),
    )
