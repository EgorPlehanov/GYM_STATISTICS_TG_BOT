"""Подтверждение добавления упражнения или подхода в draft."""

from copy import deepcopy

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.fsm.training import (
    TrainingFlowStep,
    TrainingStates,
    add_exercise_to_draft,
    add_set_to_draft,
    get_training_draft,
)
from app.bot.ui.training import is_current_training_callback, transition_training_screen

router = Router()


@router.callback_query(F.data == "accept_addition", TrainingStates.set_form)
async def accept_addition(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждает добавление только после проверки актуальности callback."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    exercise_id = next_draft.selection.exercise_id
    exercise_name = next_draft.selection.exercise_name
    weight = next_draft.selection.weight
    repetitions = next_draft.selection.repetitions
    sets_count = next_draft.selection.sets_count
    if None in (exercise_id, exercise_name, weight, repetitions, sets_count):
        raise ValueError("Недостаточно данных для добавления подхода")

    add_exercise_to_draft(next_draft, exercise_id, exercise_name)
    for _ in range(sets_count):
        add_set_to_draft(
            next_draft,
            exercise_id,
            weight=weight,
            repetitions=repetitions,
            execution_time=callback.message.date,
        )
    next_draft.selection.mode = None
    next_draft.selection.exercise_id = None
    next_draft.selection.exercise_name = None
    next_draft.selection.weight = None
    next_draft.selection.repetitions = None
    next_draft.selection.sets_count = None
    next_draft.ui.current_exercise_id = exercise_id
    next_draft.ui.current_exercise_name = exercise_name
    next_draft.ui.last_weight = weight
    next_draft.ui.last_repetitions = repetitions
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.MENU,
    )
