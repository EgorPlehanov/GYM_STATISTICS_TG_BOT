"""Ввод веса и сокращенный ввод параметров подхода."""

import re
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

from app.bot.fsm.training import (
    TrainingFlowStep,
    TrainingMode,
    TrainingStates,
    get_training_draft,
)
from app.bot.ui.training import (
    TrainingTransitionResult,
    is_current_training_callback,
    transition_training_screen,
)

router = Router()

r_float = r"\d+([.,]?\d+)?"
r_int = r"\d+"
r_separator = r"\s*[*×xх]\s*"
r_weight = rf"^\s*{r_float}\s*$"
r_weight_repetitions_sets = rf"^\s*{r_float}{r_separator}{r_int}({r_separator}{r_int})?\s*$"


@router.callback_query(F.data == "add_set", TrainingStates.menu)
async def add_set_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает ввод нового подхода текущего упражнения."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.selection.mode = TrainingMode.ADD_SET.value
    next_draft.selection.exercise_id = next_draft.ui.current_exercise_id
    next_draft.selection.exercise_name = next_draft.ui.current_exercise_name
    next_draft.selection.sets_count = 1
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.SELECT_WEIGHT,
    )


@router.inline_query(TrainingStates.select_weight)
async def inline_weight(inline_query: InlineQuery, state: FSMContext) -> None:
    """Возвращает inline-подсказки для выбора веса."""
    def generate_numbers(substring: str) -> list[float]:
        return [
            number / 100
            for number in range(0, 50100, 25)
            if substring in str(number / 100)
        ]

    offset = int(inline_query.offset) if inline_query.offset else 0
    results = [
        InlineQueryResultArticle(
            id=str(number),
            title=f"{number:.2f} кг",
            input_message_content=InputTextMessageContent(message_text=str(number)),
        )
        for number in generate_numbers(inline_query.query)
    ]
    await inline_query.answer(
        results if len(results) < 50 else results[offset : offset + 50],
        next_offset="" if len(results) < 50 else str(offset + 50),
        cache_time=0,
        is_personal=True,
    )


@router.message(F.via_bot, TrainingStates.select_weight)
@router.message(F.text.regexp(r_weight), TrainingStates.select_weight)
async def selected_weight(message: Message, state: FSMContext) -> None:
    """Сохраняет вес только после успешного перехода к вводу повторений."""
    current_draft = await get_training_draft(state)
    next_draft = deepcopy(current_draft)
    next_draft.selection.weight = float(message.text.replace(",", "."))
    result = await transition_training_screen(
        bot=message.bot,
        chat_id=message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.SELECT_REPETITIONS,
    )
    if result is TrainingTransitionResult.APPLIED:
        await message.delete()


@router.message(
    F.text.regexp(r_weight_repetitions_sets, flags=re.IGNORECASE),
    TrainingStates.menu,
)
@router.message(
    F.text.regexp(r_weight_repetitions_sets, flags=re.IGNORECASE),
    TrainingStates.select_weight,
)
@router.message(
    F.text.regexp(r_weight_repetitions_sets, flags=re.IGNORECASE),
    TrainingStates.select_repetitions,
)
@router.message(
    F.text.regexp(r_weight_repetitions_sets, flags=re.IGNORECASE),
    TrainingStates.select_sets_count,
)
@router.message(
    F.text.regexp(r_weight_repetitions_sets, flags=re.IGNORECASE),
    TrainingStates.accept_addition,
)
async def read_weight_and_repetitions(message: Message, state: FSMContext) -> None:
    """Обрабатывает ручной ввод веса, повторений и количества подходов."""
    values = re.split(r_separator, message.text, flags=re.IGNORECASE)
    weight, repetitions = values[:2]
    sets_count = values[2] if len(values) == 3 else None

    current_draft = await get_training_draft(state)
    next_draft = deepcopy(current_draft)
    if next_draft.selection.mode is None:
        next_draft.selection.mode = TrainingMode.ADD_SET.value
        next_draft.selection.exercise_id = next_draft.ui.current_exercise_id
        next_draft.selection.exercise_name = next_draft.ui.current_exercise_name
        next_draft.selection.sets_count = 1
    next_draft.selection.weight = float(weight.replace(",", "."))
    next_draft.selection.repetitions = int(repetitions)
    if sets_count is not None and int(sets_count) > 0:
        next_draft.selection.sets_count = int(sets_count)

    result = await transition_training_screen(
        bot=message.bot,
        chat_id=message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.ACCEPT_ADDITION,
    )
    if result is TrainingTransitionResult.APPLIED:
        await message.delete()


@router.callback_query(F.data == "to_weight", TrainingStates.select_exercise)
@router.callback_query(F.data == "to_weight", TrainingStates.select_repetitions)
@router.callback_query(F.data == "to_weight", TrainingStates.accept_addition)
async def to_weight(callback: CallbackQuery, state: FSMContext) -> None:
    """Переводит сценарий к выбору веса."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=draft,
        next_draft=deepcopy(draft),
        next_step=TrainingFlowStep.SELECT_WEIGHT,
    )


@router.callback_query(F.data == "repeat_set", TrainingStates.menu)
async def repeat_set(callback: CallbackQuery, state: FSMContext) -> None:
    """Предлагает подтвердить повтор последнего сохраненного подхода."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.selection.mode = TrainingMode.ADD_SET.value
    next_draft.selection.exercise_id = next_draft.ui.current_exercise_id
    next_draft.selection.exercise_name = next_draft.ui.current_exercise_name
    next_draft.selection.sets_count = 1
    next_draft.selection.weight = next_draft.ui.last_weight
    next_draft.selection.repetitions = next_draft.ui.last_repetitions
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.ACCEPT_ADDITION,
    )
