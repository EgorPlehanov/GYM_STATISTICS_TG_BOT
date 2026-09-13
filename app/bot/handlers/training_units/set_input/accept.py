from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    TrainingStates,
    add_exercise_to_draft,
    add_set_to_draft,
    get_training_draft,
    set_training_draft,
)
from app.bot.keyboards.training_kb import get_ikb_training_menu

router = Router()



@router.callback_query(F.data == 'acept_addition', TrainingStates.select_exercise)
@router.callback_query(F.data == 'acept_addition', TrainingStates.select_weight)
@router.callback_query(F.data == 'acept_addition', TrainingStates.select_repetitions)
@router.callback_query(F.data == 'acept_addition', TrainingStates.select_sets_count)
@router.callback_query(F.data == 'acept_addition', TrainingStates.acept_addition)
async def accept_addition(callback: CallbackQuery, state: FSMContext):
    """Подтверждает добавление упражнения или подхода в черновик тренировки."""
    await state.set_state(TrainingStates.menu)

    draft = await get_training_draft(state)

    exercise_id = draft.selection.exercise_id
    exercise_name = draft.selection.exercise_name
    weight = draft.selection.weight
    repetitions = draft.selection.repetitions
    sets_count = draft.selection.sets_count
    time = callback.message.date

    add_exercise_to_draft(draft, exercise_id, exercise_name)
    for _ in range(sets_count):
        add_set_to_draft(
            draft,
            exercise_id,
            weight=weight,
            repetitions=repetitions,
            execution_time=time,
        )

    draft.selection.mode = None
    draft.selection.exercise_id = None
    draft.selection.exercise_name = None
    draft.selection.weight = None
    draft.selection.repetitions = None
    draft.selection.sets_count = None
    draft.ui.current_exercise_id = exercise_id
    draft.ui.current_exercise_name = exercise_name
    draft.ui.last_weight = weight
    draft.ui.last_repetitions = repetitions
    await set_training_draft(state, draft)
    
    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_training_menu(
            is_add_add_set_button=True,
            repeat_set_button_text=f"{str(weight).rstrip('0').rstrip('.')}×{repetitions}",
        )
    )

