from copy import deepcopy
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
    bot_training_to_draft,
    draft_from_json,
    draft_to_bot_training,
    draft_to_json,
    get_training_draft,
    has_draft_exercises,
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
    draft = await get_training_draft(state)

    last_weight = str(draft.ui.last_weight or "").rstrip("0").rstrip(".")
    last_repetitions = draft.ui.last_repetitions or ""

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
        None. Если дата тренировки еще не выбрана, состояние не меняется.
    """
    draft = await get_training_draft(state)
    if draft.training.training_date is None:
        return

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
    changed_draft = bot_training_to_draft(result.training)
    is_exists = result.exists

    draft = await get_training_draft(state)
    changed_draft.suggestions = deepcopy(draft.suggestions)
    changed_draft.ui = deepcopy(draft.ui)
    changed_draft.ui.current_exercise_id = None
    changed_draft.ui.current_exercise_name = None
    changed_draft.ui.last_weight = None
    changed_draft.ui.last_repetitions = None
    if draft.training.training_date is None:
        await set_training_draft(state, changed_draft)
    else:
        if draft.training.training_date == training_date.isoformat():
            return
        if is_exists:
            await state.set_state(TrainingStates.change_date_acept)
            await state.update_data(
                changed_training_draft=draft_to_json(changed_draft),
            )
            await callback.message.edit_text(
                text=await get_formatted_state_date(state),
                reply_markup = get_ikb_changed_date(
                    other_date=training_date
                )
            )
            return False
        else:
            draft.training.training_date = training_date.isoformat()
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
    draft = await get_training_draft(state)
    if not draft.suggestions.training_dates:
        async with BotApiClient() as api_client:
            training_date = await api_client.get_training_dates(callback.from_user.id)
        draft.suggestions.training_dates = [
            item.isoformat() for item in training_date
        ]
        await set_training_draft(state, draft)
    else:
        training_date = [
            date.fromisoformat(item)
            for item in draft.suggestions.training_dates
        ]

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
    draft = await get_training_draft(state)

    selected, selected_date = await DialogCalendar(
        training_date=[
            date.fromisoformat(item)
            for item in draft.suggestions.training_dates
        ]
    ).process_selection(callback, callback_data)

    if selected:
        await state.set_state(TrainingStates.menu)

        await _clear_selection_mode_if_training_started(state)
        if (await init_training_by_date(selected_date, callback, state)) is False:
            return

        await _render_training_menu(callback, state)



@router.callback_query(F.data == 'to_date_menu', TrainingStates.select_date)
@router.callback_query(F.data == 'to_date_menu', TrainingStates.change_date_acept)
async def back_to_date_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает пользователя в меню выбора даты."""
    await state.set_state(TrainingStates.select_date)

    draft = await get_training_draft(state)
    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(
            is_back_to_menu=draft.training.training_date is not None,
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
    draft = await get_training_draft(state)
    async with BotApiClient() as api_client:
        await api_client.save_training(
            telegram_id=callback.from_user.id,
            training=draft_to_bot_training(draft),
        )

    changed_training_draft = (await state.get_data()).get("changed_training_draft")
    draft = draft_from_json(changed_training_draft)
    draft.selection.mode = None
    draft.selection.exercise_id = None
    draft.selection.exercise_name = None
    await set_training_draft(state, draft)
    await state.update_data(
        changed_training_draft=None,
    )

    await state.set_state(TrainingStates.menu)
    draft = await get_training_draft(state)

    last_weight = str(draft.ui.last_weight or "").rstrip("0").rstrip(".")
    last_repetitions = draft.ui.last_repetitions or ""

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
    changed_draft = draft_from_json(user_data.get("changed_training_draft"))
    training_date = changed_draft.training.training_date
    training_id = changed_draft.training.training_id

    if training_id is not None:
        async with BotApiClient() as api_client:
            await api_client.delete_training(training_id)

    draft = await get_training_draft(state)
    draft.training.training_date = training_date
    draft.training.training_id = None
    await set_training_draft(state, draft)

    await state.update_data(changed_training_draft=None)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(is_back_to_menu=True),
    )

