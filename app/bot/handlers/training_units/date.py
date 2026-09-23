"""Выбор и изменение даты тренировки."""

from copy import deepcopy
from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.client import BotApiClient
from app.bot.fsm.training import (
    TrainingDateConflict,
    TrainingDraft,
    TrainingFlowStep,
    TrainingMode,
    TrainingStates,
    bot_training_to_draft,
    draft_to_bot_training,
    get_training_draft,
    set_draft_training_dates,
)
from app.bot.ui.training import (
    is_current_training_callback,
    replace_after_backend,
    transition_training_screen,
)
from app.bot.ui.training.calendar import (
    TrainingCalendarAction,
    TrainingCalendarCallback,
    resolve_training_calendar_interaction,
)

from .redirect_result import delete_removed_training_redirect_messages

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
        if (
            current_draft.training.training_id is None
            or result.training.training_id != current_draft.training.training_id
        ):
            next_draft = deepcopy(current_draft)
            next_draft.ui.date_conflict = TrainingDateConflict(training=loaded_draft.training)
            _clear_calendar_month(next_draft)
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
        _set_draft_training_date(next_draft, training_date.isoformat())
    if next_draft.training.training_date is not None:
        next_draft.selection.mode = None
    next_draft.ui.date_conflict = None
    next_draft.edit.replace_training_id = None
    _clear_calendar_month(next_draft)
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.MENU,
    )


@router.callback_query(TrainingCalendarCallback.filter(), TrainingStates.select_date)
async def process_training_calendar(
    callback: CallbackQuery,
    callback_data: TrainingCalendarCallback,
    state: FSMContext,
) -> None:
    """Обрабатывает навигацию нового календаря или выбор даты."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    await callback.answer()
    if callback_data.action is TrainingCalendarAction.IGNORE:
        return

    interaction = resolve_training_calendar_interaction(callback_data)
    if interaction.selected_date is not None:
        await _select_date(callback, state, interaction.selected_date)
        return

    next_draft = deepcopy(draft)
    next_draft.ui.calendar_view = interaction.view
    next_draft.ui.calendar_year = interaction.year
    next_draft.ui.calendar_month = interaction.month
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.SELECT_DATE,
    )


@router.callback_query(F.data == "to_date_menu", TrainingStates.change_date_accept)
async def back_to_date_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает к календарю после отмены разрешения конфликта дат."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    next_draft = deepcopy(draft)
    next_draft.ui.date_conflict = None
    _clear_calendar_month(next_draft)
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
    _clear_calendar_month(next_draft)
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
        save_result = await api_client.save_training(
            telegram_id=callback.from_user.id,
            training=draft_to_bot_training(draft),
            replace_training_id=draft.edit.replace_training_id,
        )
    next_draft = deepcopy(draft)
    next_draft.training = deepcopy(conflict.training)
    next_draft.selection.mode = None
    next_draft.selection.exercise_id = None
    next_draft.selection.exercise_name = None
    next_draft.ui.date_conflict = None
    next_draft.edit.replace_training_id = None
    next_draft.edit.original_training_date = None
    set_draft_training_dates(next_draft, save_result.training_dates)
    _clear_calendar_month(next_draft)
    await replace_after_backend(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        draft=next_draft, step=TrainingFlowStep.MENU,
    )
    await delete_removed_training_redirect_messages(
        bot=callback.bot,
        deleted_redirect_messages=save_result.deleted_redirect_messages,
    )


@router.callback_query(F.data == "changed_to_current_date", TrainingStates.change_date_accept)
async def changed_to_current_date(callback: CallbackQuery, state: FSMContext) -> None:
    """Готовит атомарную замену конфликтующей тренировки при финальном сохранении.

    В БД ничего не меняется до нажатия пользователем финальной кнопки сохранения:
    текущий draft сохраняет свой id и данные, а id конфликтующей тренировки
    записывается как отложенная операция.
    """
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    conflict = draft.ui.date_conflict
    if conflict is None:
        raise ValueError("Для замены даты нужен date_conflict")
    if conflict.training.training_id is None:
        raise ValueError("Для замены даты нужен id конфликтующей тренировки")
    next_draft = deepcopy(draft)
    _set_draft_training_date(next_draft, conflict.training.training_date)
    next_draft.selection.mode = None
    next_draft.edit.replace_training_id = conflict.training.training_id
    next_draft.ui.date_conflict = None
    _clear_calendar_month(next_draft)
    await replace_after_backend(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        draft=next_draft, step=TrainingFlowStep.MENU,
    )


def _clear_calendar_month(draft: TrainingDraft) -> None:
    """Очищает UI-параметры месяца после завершения работы с календарем."""
    draft.ui.calendar_view = None
    draft.ui.calendar_year = None
    draft.ui.calendar_month = None


def _set_draft_training_date(draft: TrainingDraft, training_date: str) -> None:
    """Запоминает дату в БД при первом переносе и сбрасывает ее при возврате."""
    original_date = draft.edit.original_training_date
    if original_date is None and draft.training.training_id is not None:
        original_date = draft.training.training_date
    draft.training.training_date = training_date
    draft.edit.original_training_date = (
        original_date if original_date != training_date else None
    )
