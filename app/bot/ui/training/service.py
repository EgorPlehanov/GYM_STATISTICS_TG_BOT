"""Единые операции с главным Telegram-сообщением тренировки."""

from datetime import date
from enum import Enum

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from app.bot.fsm.training import (
    TrainingDraft,
    TrainingFlowStep,
    flow_step_from_state,
    set_training_draft,
    state_from_flow_step,
)
from app.bot.telegram.message_operations import (
    ControlledMessageOperationResult,
    delete_controlled_message,
    edit_controlled_message_reply_markup,
    edit_controlled_message_text,
)

from .renderer import render_training_view


class TrainingTransitionResult(str, Enum):
    """Результат попытки изменить главный интерфейс тренировки."""

    APPLIED = "applied"
    RECOVERED = "recovered"


async def is_current_training_callback(
    callback: CallbackQuery,
    draft: TrainingDraft,
) -> bool:
    """Проверяет, что callback пришел от актуального интерфейсного сообщения."""
    message = callback.message
    if message is None or draft.ui.message_id is None:
        await callback.answer("Экран тренировки устарел. Откройте /training.", show_alert=True)
        return False
    if message.message_id != draft.ui.message_id:
        await callback.answer("Этот экран уже не актуален. Откройте /training.", show_alert=True)
        return False
    return True


async def start_training_screen(
    *,
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    draft: TrainingDraft,
) -> None:
    """Отправляет первый экран и только затем сохраняет новый сценарий."""
    _ensure_calendar_month(draft)
    view = render_training_view(draft, TrainingFlowStep.SELECT_DATE)
    message = await bot.send_message(
        chat_id=chat_id,
        text=view.text,
        reply_markup=view.reply_markup,
    )
    draft.ui.message_id = message.message_id
    await set_training_draft(state, draft)
    await state.set_state(state_from_flow_step(TrainingFlowStep.SELECT_DATE))


async def transition_training_screen(
    *,
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    current_draft: TrainingDraft,
    next_draft: TrainingDraft,
    next_step: TrainingFlowStep,
) -> TrainingTransitionResult:
    """Показывает следующий экран обратимого действия или восстанавливает текущий.

    Draft и FSM меняются только после успешного обновления исходного сообщения.
    Если исходное сообщение уже удалено, отправляется его текущая версия, а
    пользовательское действие не применяется.
    """
    current_step = flow_step_from_state(await state.get_state())
    _ensure_calendar_month(next_draft, step=next_step)
    next_view = render_training_view(next_draft, next_step)
    message_id = current_draft.ui.message_id

    if message_id is None:
        await _recover_current_screen(
            bot=bot,
            chat_id=chat_id,
            state=state,
            draft=current_draft,
            step=current_step,
        )
        return TrainingTransitionResult.RECOVERED

    operation_result = await edit_controlled_message_text(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        text=next_view.text,
        reply_markup=next_view.reply_markup,
    )
    if operation_result is ControlledMessageOperationResult.MESSAGE_UNAVAILABLE:
        await _recover_current_screen(
            bot=bot,
            chat_id=chat_id,
            state=state,
            draft=current_draft,
            step=current_step,
        )
        return TrainingTransitionResult.RECOVERED

    next_draft.ui.message_id = message_id
    await set_training_draft(state, next_draft)
    await state.set_state(state_from_flow_step(next_step))
    return TrainingTransitionResult.APPLIED


async def replace_after_backend(
    *,
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    draft: TrainingDraft,
    step: TrainingFlowStep,
) -> None:
    """Показывает фактический результат уже завершенной backend-операции.

    Draft и FSM сохраняются до обращения к Telegram, потому что backend уже
    изменил источник истины. При удаленном сообщении создается новое.
    """
    await set_training_draft(state, draft)
    await state.set_state(state_from_flow_step(step))
    await _replace_or_send(
        bot=bot,
        chat_id=chat_id,
        draft=draft,
        step=step,
    )
    await set_training_draft(state, draft)


async def show_or_recover_target(
    *,
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    draft: TrainingDraft,
    step: TrainingFlowStep,
) -> None:
    """Принудительно заменяет интерфейсный экран при повторном запуске сценария.

    Команда ``/training`` должна вернуть пользователю видимый интерфейс даже если
    прежнее сообщение было удалено только в его Telegram-клиенте. Такое удаление
    не видно Bot API: ``editMessageText`` завершается успешно, хотя пользователь
    сообщения уже не видит. Поэтому этот путь всегда отправляет новый экран и
    затем удаляет прежний экземпляр на стороне Telegram.
    """
    _ensure_calendar_month(draft, step=step)
    previous_message_id = draft.ui.message_id
    view = render_training_view(draft, step)
    message = await bot.send_message(
        chat_id=chat_id,
        text=view.text,
        reply_markup=view.reply_markup,
    )
    draft.ui.message_id = message.message_id
    await set_training_draft(state, draft)
    await state.set_state(state_from_flow_step(step))
    await delete_training_message(
        bot=bot,
        chat_id=chat_id,
        message_id=previous_message_id,
    )


async def delete_training_message(
    *,
    bot: Bot,
    chat_id: int,
    message_id: int | None,
) -> None:
    """Удаляет главное сообщение, игнорируя уже удаленный интерфейс."""
    if message_id is None:
        return
    await delete_controlled_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
    )


async def replace_training_markup(
    *,
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    draft: TrainingDraft,
    step: TrainingFlowStep,
    reply_markup: InlineKeyboardMarkup | None,
) -> None:
    """Обновляет клавиатуру главного сообщения или восстанавливает его целиком."""
    if draft.ui.message_id is not None:
        operation_result = await edit_controlled_message_reply_markup(
            bot=bot,
            chat_id=chat_id,
            message_id=draft.ui.message_id,
            reply_markup=reply_markup,
        )
        if operation_result is not ControlledMessageOperationResult.MESSAGE_UNAVAILABLE:
            return

    view = render_training_view(draft, step)
    message = await bot.send_message(
        chat_id=chat_id,
        text=view.text,
        reply_markup=reply_markup,
    )
    draft.ui.message_id = message.message_id
    await set_training_draft(state, draft)


async def _replace_or_send(
    *,
    bot: Bot,
    chat_id: int,
    draft: TrainingDraft,
    step: TrainingFlowStep,
) -> None:
    """Редактирует актуальный экран или отправляет новый при его отсутствии."""
    view = render_training_view(draft, step)
    if draft.ui.message_id is not None:
        operation_result = await edit_controlled_message_text(
            bot=bot,
            chat_id=chat_id,
            message_id=draft.ui.message_id,
            text=view.text,
            reply_markup=view.reply_markup,
        )
        if operation_result is not ControlledMessageOperationResult.MESSAGE_UNAVAILABLE:
            return

    message = await bot.send_message(
        chat_id=chat_id,
        text=view.text,
        reply_markup=view.reply_markup,
    )
    draft.ui.message_id = message.message_id


async def _recover_current_screen(
    *,
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    draft: TrainingDraft,
    step: TrainingFlowStep,
) -> None:
    """Отправляет новый экземпляр текущего экрана и сохраняет его id."""
    _ensure_calendar_month(draft, step=step)
    draft.ui.message_id = None
    await _replace_or_send(bot=bot, chat_id=chat_id, draft=draft, step=step)
    await set_training_draft(state, draft)


def _ensure_calendar_month(
    draft: TrainingDraft,
    *,
    step: TrainingFlowStep = TrainingFlowStep.SELECT_DATE,
) -> None:
    """Инициализирует открытый месяц перед показом календаря."""
    if step is not TrainingFlowStep.SELECT_DATE:
        return
    if draft.ui.calendar_year is not None and draft.ui.calendar_month is not None:
        return
    today = date.today()
    draft.ui.calendar_year = today.year
    draft.ui.calendar_month = today.month
