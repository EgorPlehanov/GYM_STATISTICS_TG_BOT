"""Выбор упражнения для тренировки."""

from copy import deepcopy

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
from app.bot.fsm.training import (
    TrainingDraft,
    TrainingFlowStep,
    TrainingMode,
    TrainingStates,
    TrainingSuggestedExercise,
    get_training_draft,
)
from app.bot.keyboards.keyboards_types import PaginationAction
from app.bot.keyboards.training_kb import TrainingExercisePagination
from app.bot.ui.training import (
    TrainingTransitionResult,
    is_current_training_callback,
    transition_training_screen,
)

router = Router()

# Временный payload для inline-выбора упражнения. Позже будет заменен на
# устойчивый signed/Redis-backed payload.
key = Fernet.generate_key()
cipher = Fernet(key)


@router.callback_query(F.data == "add_exercise", TrainingStates.menu)
async def add_exercise_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает выбор упражнения для добавления в тренировку."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.selection.mode = TrainingMode.ADD_EXERCISE.value
    next_draft.selection.exercise_id = None
    next_draft.selection.exercise_name = None
    next_draft.selection.weight = None
    next_draft.selection.repetitions = None
    next_draft.selection.sets_count = 1
    next_draft.ui.exercise_selection_return_step = None
    next_draft.ui.exercise_page = 0
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.SELECT_EXERCISE,
    )


@router.callback_query(
    TrainingExercisePagination.filter(F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])),
    TrainingStates.select_exercise,
)
async def selected_exercise_pagination(
    callback: CallbackQuery, callback_data: TrainingExercisePagination, state: FSMContext
) -> None:
    """Переключает страницу списка частых упражнений."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    page = int(callback_data.page)
    if callback_data.action is PaginationAction.PREV:
        page = max(page - 1, 0)
    else:
        page += 1
    next_draft.ui.exercise_page = page
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.SELECT_EXERCISE,
    )


@router.callback_query(
    TrainingExercisePagination.filter(F.action == PaginationAction.SET),
    TrainingStates.select_exercise,
)
async def selected_exercise(
    callback: CallbackQuery, callback_data: TrainingExercisePagination, state: FSMContext
) -> None:
    """Сохраняет выбранное упражнение и открывает форму подхода."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    exercise_id = int(callback_data.exercise_id)
    exercise = next(
        item for item in next_draft.suggestions.most_frequent_exercises
        if item.id == exercise_id
    )
    next_draft.suggestions.most_frequent_exercises.remove(exercise)
    next_draft.suggestions.most_frequent_exercises.insert(0, exercise)
    next_draft.selection.exercise_id = exercise_id
    next_draft.selection.exercise_name = exercise.name
    _apply_exercise_suggestion(next_draft)
    next_draft.ui.exercise_page = 0
    next_draft.ui.exercise_selection_return_step = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.SET_FORM,
    )


@router.callback_query(F.data == "form_select_exercise", TrainingStates.set_form)
async def select_exercise_from_form(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает выбор упражнения с возможностью вернуться к заполненной форме."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.ui.exercise_page = 0
    next_draft.ui.exercise_selection_return_step = TrainingFlowStep.SET_FORM
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.SELECT_EXERCISE,
    )


@router.callback_query(
    F.data == "form_cancel_exercise_selection",
    TrainingStates.select_exercise,
)
async def cancel_exercise_selection_from_form(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Возвращает к форме, не меняя ранее заполненные значения."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.ui.exercise_selection_return_step = None
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.SET_FORM,
    )


@router.inline_query(TrainingStates.select_exercise)
async def inline_exercise_search(inline_query: InlineQuery, state: FSMContext) -> None:
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
    results = [
        InlineQueryResultArticle(
            id=str(exercise.id), title=exercise.name, description=exercise.description,
            input_message_content=InputTextMessageContent(
                message_text=cipher.encrypt(str(exercise.id).encode()),
                parse_mode=None,
            ),
        )
        for exercise in exercises
    ]
    await inline_query.answer(
        results, next_offset="" if len(results) < 50 else str(offset + 50),
        cache_time=0, is_personal=True,
    )


@router.message(F.via_bot, TrainingStates.select_exercise)
async def inline_selected_exercise(message: Message, state: FSMContext) -> None:
    """Применяет выбранное через inline-поиск упражнение после UI-перехода."""
    exercise_id = int(cipher.decrypt(message.text).decode())
    async with BotApiClient() as api_client:
        exercise = await api_client.get_exercise(exercise_id=exercise_id)
    current_draft = await get_training_draft(state)
    next_draft = deepcopy(current_draft)
    items = next_draft.suggestions.most_frequent_exercises
    items[:] = [item for item in items if item.id != exercise.id]
    items.insert(
        0,
        TrainingSuggestedExercise(
            id=exercise.id,
            name=exercise.name,
            description=exercise.description,
        ),
    )
    next_draft.selection.exercise_id = exercise.id
    next_draft.selection.exercise_name = exercise.name
    _apply_exercise_suggestion(next_draft)
    next_draft.ui.exercise_page = 0
    next_draft.ui.exercise_selection_return_step = None
    result = await transition_training_screen(
        bot=message.bot, chat_id=message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.SET_FORM,
    )
    if result is TrainingTransitionResult.APPLIED:
        await message.delete()


def _apply_exercise_suggestion(draft: TrainingDraft) -> None:
    """Применяет подсказку следующего подхода после выбора упражнения."""
    from app.bot.fsm.training import get_weight_repetitions_modes_values_from_draft
    from app.core.weights import normalize_weight

    values = get_weight_repetitions_modes_values_from_draft(
        draft,
        is_weight=True,
        is_repetitions=True,
    )
    if not isinstance(values, tuple):
        draft.selection.weight = None
        draft.selection.repetitions = None
        return
    weight, repetitions = values
    draft.selection.weight = normalize_weight(weight) if weight else None
    draft.selection.repetitions = int(repetitions) if repetitions else None
