from datetime import date, datetime

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.client import BotApiClient
from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    TrainingMode,
    TrainingStates,
    get_training_draft,
    has_draft_exercises,
    set_legacy_exercise_data,
    set_training_draft,
)
from app.bot.keyboards.training_kb import (
    DialogCalendar,
    DialogCalendarCallback,
    get_ikb_changed_date,
    get_ikb_select_date,
    get_ikb_training_menu,
)

router = Router()


async def _render_training_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Обновляет основное сообщение меню тренировки после выбора даты.

    Args:
        callback: callback query с сообщением, которое нужно отредактировать.
        state: FSMContext текущего сценария тренировки.

    Returns:
        None. Telegram-сообщение обновляется через Bot API.
    """
    user_data: dict[str, int | dict] = await state.get_data()
    draft = await get_training_draft(state)

    last_weight = str(user_data.get("last_weight", "")).rstrip("0").rstrip(".")
    last_repetitions = user_data.get("last_repetitions", "")

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_training_menu(
            is_add_edit_button=has_draft_exercises(draft),
            is_add_add_set_button=draft.selection.exercise_id is not None,
            repeat_set_button_text=f"{last_weight}×{last_repetitions}",
        ),
    )


async def _clear_selection_mode_if_training_started(state: FSMContext) -> None:
    """Сбрасывает режим текущего ввода, если FSM draft уже можно собрать.

    Args:
        state: FSMContext текущего сценария тренировки.

    Returns:
        None. Если тренировка еще не выбрана и `exercise_data` отсутствует,
        состояние не меняется.
    """
    user_data = await state.get_data()
    if user_data.get("exercise_data") is None:
        return

    draft = await get_training_draft(state)
    draft.selection.mode = None
    await set_training_draft(state, draft)


async def init_training_by_date(
    training_date: date | datetime,
    callback: CallbackQuery,
    state: FSMContext,
) -> bool | None:
    """Загружает тренировку по дате и обновляет FSM draft.

    Args:
        training_date: выбранная пользователем дата тренировки.
        callback: callback query с сообщением, которое нужно обновить при конфликте.
        state: FSMContext текущего сценария тренировки.

    Returns:
        False, если выбранная дата конфликтует с другой тренировкой и обработчик
        должен остановиться. В остальных случаях возвращает None.
    """
    if isinstance(training_date, datetime):
        training_date = training_date.date()

    async with BotApiClient() as api_client:
        result = await api_client.get_training_by_date(
            telegram_id=callback.from_user.id,
            training_date=training_date,
        )
    changed_exercise_data = result.training_data
    is_exists = result.exists

    user_data: dict[str, int | dict] = await state.get_data()
    cur_exercise_data = user_data.get("exercise_data")
    if cur_exercise_data is None:
        await set_legacy_exercise_data(state, changed_exercise_data)
        draft = await get_training_draft(state)
        draft.training.training_date = training_date
        await set_training_draft(state, draft)
    else:
        draft = await get_training_draft(state)
        if draft.training.training_date == training_date.isoformat():
            return
        if is_exists:
            await state.set_state(TrainingStates.change_date_acept)
            await state.update_data(changed_exercise_data=changed_exercise_data)
            await callback.message.edit_text(
                text=await get_formatted_state_date(state),
                reply_markup = get_ikb_changed_date(
                    other_date=training_date
                )
            )
            return False
        else:
            draft.training.training_date = training_date
            await set_training_draft(state, draft)



@router.callback_query(
    F.data == 'today',
    TrainingStates.select_date
)
async def selected_date_today(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбирает текущую дату для тренировки."""
    await state.set_state(TrainingStates.menu)

    training_date = datetime.now().date()

    await _clear_selection_mode_if_training_started(state)
    if (await init_training_by_date(training_date, callback, state)) is False:
        return

    await _render_training_menu(callback, state)



@router.callback_query(
    F.data == 'other_date',
    TrainingStates.select_date
)
async def selected_date_other(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает inline-календарь для выбора другой даты."""
    user_data = await state.get_data()
    if user_data.get("training_date") is None:
        async with BotApiClient() as api_client:
            training_date = await api_client.get_training_dates(callback.from_user.id)
        await state.update_data(training_date=training_date)
    else:
        training_date = user_data.get("training_date")

    await callback.message.edit_reply_markup(
        reply_markup=await DialogCalendar(training_date=training_date).start_calendar()
    )



@router.callback_query(
    DialogCalendarCallback.filter()
)
async def process_dialog_calendar(
    callback: CallbackQuery,
    callback_data: CallbackData,
    state: FSMContext,
) -> None:
    """Обрабатывает выбор даты в inline-календаре."""
    user_data = await state.get_data()

    selected, date = await DialogCalendar(
        training_date=user_data.get("training_date")
    ).process_selection(callback, callback_data)

    if selected:
        await state.set_state(TrainingStates.menu)

        await _clear_selection_mode_if_training_started(state)
        if (await init_training_by_date(date, callback, state)) is False:
            return

        await _render_training_menu(callback, state)



@router.callback_query(F.data == 'to_date_menu', TrainingStates.select_date)
@router.callback_query(F.data == 'to_date_menu', TrainingStates.change_date_acept)
async def back_to_date_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает пользователя в меню выбора даты."""
    await state.set_state(TrainingStates.select_date)

    user_data: dict[str, int | dict] = await state.get_data()
    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(
            is_back_to_menu=user_data.get('exercise_data') is not None,
        ),
    )
    


@router.callback_query(
    F.data == 'edit_date',
    TrainingStates.edit_menu
)
async def open_edit_date(callback: CallbackQuery, state: FSMContext):
    """Открывает выбор даты в режиме редактирования тренировки."""
    await state.set_state(TrainingStates.select_date)

    draft = await get_training_draft(state)
    draft.selection.mode = TrainingMode.EDIT_DATE.value
    await set_training_draft(state, draft)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(is_back_to_menu=True),
    )



@router.callback_query(
    F.data == 'save_and_go',
    TrainingStates.change_date_acept
)
async def save_current_training_and_open_selected_date(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Сохраняет текущий черновик и открывает тренировку на выбранную дату."""
    user_data: dict[str, int | dict] = await state.get_data()
    exercise_data = user_data.get("exercise_data")
    async with BotApiClient() as api_client:
        await api_client.save_training(exercise_data)

    changed_exercise_data = user_data.get("changed_exercise_data")
    await set_legacy_exercise_data(state, changed_exercise_data)
    draft = await get_training_draft(state)
    draft.selection.mode = None
    draft.selection.exercise_id = None
    draft.selection.exercise_name = None
    await set_training_draft(state, draft)
    await state.update_data(
        changed_exercise_data=None,
        exercise_id=None,
        exercise_name=None,
    )

    await state.set_state(TrainingStates.menu)
    draft = await get_training_draft(state)

    last_weight = str(user_data.get("last_weight", "")).rstrip("0").rstrip(".")
    last_repetitions = user_data.get("last_repetitions", "")

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_training_menu(
            is_add_edit_button=has_draft_exercises(draft),
            is_add_add_set_button=False,
            repeat_set_button_text=f"{last_weight}×{last_repetitions}",
        ),
    )




@router.callback_query(
    F.data == 'changed_to_current_date',
    TrainingStates.change_date_acept
)
async def changed_to_current_date(callback: CallbackQuery, state: FSMContext):
    """Удаляет тренировку на выбранную дату и переносит туда текущий черновик."""
    await state.set_state(TrainingStates.menu)

    user_data: dict[str, int | dict] = await state.get_data()
    changed_exercise_data = user_data.get("changed_exercise_data")
    training_date = changed_exercise_data.get("date")
    training_id = changed_exercise_data.get("id")

    async with BotApiClient() as api_client:
        await api_client.delete_training(training_id)

    draft = await get_training_draft(state)
    draft.training.training_date = training_date
    await set_training_draft(state, draft)

    await state.update_data(changed_exercise_data=None)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(is_back_to_menu=True),
    )

