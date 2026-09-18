"""Выбор и изменение даты тренировки."""

from copy import deepcopy
from datetime import date, datetime

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.client import BotApiClient
from app.bot.fsm.training import (
    TrainingDateConflict,
    TrainingFlowStep,
    TrainingMode,
    TrainingStates,
    bot_training_to_draft,
    draft_to_bot_training,
    get_training_draft,
    set_training_draft,
)
from app.bot.keyboards.training_kb import DialogCalendar, DialogCalendarCallback
from app.bot.ui.training import (
    is_current_training_callback,
    replace_after_backend,
    replace_training_markup,
    transition_training_screen,
)

router = Router()


async def _select_date(
    callback: CallbackQuery, state: FSMContext, training_date: date
) -> None:
    """Загружает дату и переводит сценарий в меню или подтверждение конфликта."""
    current_draft = await get_training_draft(state)
    async with BotApiClient() as api_client:
        result = await api_client.get_training_by_date(
            telegram_id=callback.from_user.id, training_date=training_date
        )
    loaded_draft = bot_training_to_draft(result.training)

    if current_draft.training.training_date is not None and result.exists:
        if current_draft.training.training_date == training_date.isoformat():
            return
        next_draft = deepcopy(current_draft)
        next_draft.ui.date_conflict = TrainingDateConflict(training=loaded_draft.training)
        await transition_training_screen(
            bot=callback.bot, chat_id=callback.message.chat.id, state=state,
            current_draft=current_draft, next_draft=next_draft,
            next_step=TrainingFlowStep.CHANGE_DATE_ACCEPT,
        )
        return

    next_draft = deepcopy(current_draft)
    if current_draft.training.training_date is None:
        next_draft.training = loaded_draft.training
    else:
        next_draft.training.training_date = training_date.isoformat()
    if next_draft.training.training_date is not None:
        next_draft.selection.mode = None
    next_draft.ui.date_conflict = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.MENU,
    )


@router.callback_query(F.data == "today", TrainingStates.select_date)
async def selected_date_today(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбирает текущую дату для тренировки."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    await _select_date(callback, state, datetime.now().date())


@router.callback_query(F.data == "other_date", TrainingStates.select_date)
async def selected_date_other(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает календарь выбора даты.

    Календарь пока использует собственный callback-протокол. Его полный перевод
    на renderer выделен отдельной задачей рефакторинга календаря.
    """
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    if not draft.suggestions.training_dates:
        async with BotApiClient() as api_client:
            dates = await api_client.get_training_dates(callback.from_user.id)
        draft.suggestions.training_dates = [item.isoformat() for item in dates]
        await set_training_draft(state, draft)
    calendar_markup = await DialogCalendar(
        training_date=[date.fromisoformat(item) for item in draft.suggestions.training_dates]
    ).start_calendar()
    await replace_training_markup(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        draft=draft,
        step=TrainingFlowStep.SELECT_DATE,
        reply_markup=calendar_markup,
    )


@router.callback_query(DialogCalendarCallback.filter())
async def process_dialog_calendar(
    callback: CallbackQuery, callback_data: CallbackData, state: FSMContext
) -> None:
    """Обрабатывает календарь и применяет выбранную дату."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    selected, selected_date, markup = await DialogCalendar(
        training_date=[date.fromisoformat(item) for item in draft.suggestions.training_dates]
    ).get_selection_view(callback_data)
    if selected:
        await _select_date(callback, state, selected_date)
    elif markup is not None:
        await replace_training_markup(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            state=state,
            draft=draft,
            step=TrainingFlowStep.SELECT_DATE,
            reply_markup=markup,
        )


@router.callback_query(F.data == "to_date_menu", TrainingStates.select_date)
@router.callback_query(F.data == "to_date_menu", TrainingStates.change_date_accept)
async def back_to_date_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает в меню выбора даты."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    next_draft = deepcopy(draft)
    next_draft.ui.date_conflict = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=draft, next_draft=next_draft,
        next_step=TrainingFlowStep.SELECT_DATE,
    )


@router.callback_query(F.data == "edit_date", TrainingStates.edit_menu)
async def open_edit_date(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает выбор даты в режиме редактирования."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    next_draft = deepcopy(draft)
    next_draft.selection.mode = TrainingMode.EDIT_DATE.value
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=draft, next_draft=next_draft,
        next_step=TrainingFlowStep.SELECT_DATE,
    )


@router.callback_query(F.data == "save_and_go", TrainingStates.change_date_accept)
async def save_current_training_and_open_selected_date(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Сохраняет текущую тренировку и открывает существующую на другой дате."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    conflict = draft.ui.date_conflict
    if conflict is None:
        raise ValueError("Для смены даты нужен date_conflict")
    async with BotApiClient() as api_client:
        await api_client.save_training(
            telegram_id=callback.from_user.id,
            training=draft_to_bot_training(draft),
        )
    next_draft = deepcopy(draft)
    next_draft.training = deepcopy(conflict.training)
    next_draft.selection.mode = None
    next_draft.selection.exercise_id = None
    next_draft.selection.exercise_name = None
    next_draft.ui.date_conflict = None
    await replace_after_backend(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        draft=next_draft, step=TrainingFlowStep.MENU,
    )


@router.callback_query(F.data == "changed_to_current_date", TrainingStates.change_date_accept)
async def changed_to_current_date(callback: CallbackQuery, state: FSMContext) -> None:
    """Удаляет конфликтующую тренировку и переносит туда текущий draft."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    conflict = draft.ui.date_conflict
    if conflict is None:
        raise ValueError("Для замены даты нужен date_conflict")
    if conflict.training.training_id is not None:
        async with BotApiClient() as api_client:
            await api_client.delete_training(conflict.training.training_id)
    next_draft = deepcopy(draft)
    next_draft.training.training_date = conflict.training.training_date
    next_draft.training.training_id = None
    next_draft.ui.date_conflict = None
    await replace_after_backend(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        draft=next_draft, step=TrainingFlowStep.MENU,
    )
