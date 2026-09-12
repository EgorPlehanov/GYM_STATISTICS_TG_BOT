from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    TrainingStates,
    add_exercise,
    add_set,
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

    user_data: dict[str, int | dict] = await state.get_data()
    draft = await get_training_draft(state)

    exercise_data = user_data.get('exercise_data')
    exercise_id = draft.selection.exercise_id
    exercise_name = draft.selection.exercise_name
    weight = draft.selection.weight
    repetitions = draft.selection.repetitions
    sets_count = draft.selection.sets_count
    time = callback.message.date
    
    add_exercise(exercise_data, exercise_id, exercise_name)
    for _ in range(sets_count):
        add_set(exercise_data, exercise_id, weight, repetitions, time)

    await state.update_data(exercise_data=exercise_data)
    draft = await get_training_draft(state)
    draft.selection.mode = None
    draft.selection.exercise_id = None
    draft.selection.exercise_name = None
    draft.selection.weight = None
    draft.selection.repetitions = None
    draft.selection.sets_count = None
    await set_training_draft(state, draft)
    await state.update_data(
        exercise_id=exercise_id,
        exercise_name=exercise_name,
        last_weight=weight,
        last_repetitions=repetitions,
    )
    
    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_training_menu(
            is_add_add_set_button=True,
            repeat_set_button_text=f"{str(weight).rstrip('0').rstrip('.')}×{repetitions}",
        )
    )

