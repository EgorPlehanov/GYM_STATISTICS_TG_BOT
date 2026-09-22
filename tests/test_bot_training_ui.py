"""Тесты renderer-а и восстановления главного сообщения тренировки."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import EditMessageText

from app.bot.fsm.training import (
    TrainingCalendarView,
    TrainingDraft,
    TrainingDraftData,
    TrainingFlowStep,
    TrainingMode,
    TrainingStates,
    draft_to_json,
)
from app.bot.ui.training import (
    TrainingTransitionResult,
    render_training_view,
    replace_after_backend,
    show_or_recover_target,
    transition_training_screen,
)


class FakeFSMContext:
    """Минимальный FSMContext для проверки UI-переходов."""

    def __init__(self, draft: TrainingDraft, state_name: str) -> None:
        """Инициализирует draft и активное aiogram-состояние."""
        self.data = {"training_draft": draft_to_json(draft)}
        self.state_name = state_name

    async def get_data(self) -> dict:
        """Возвращает данные FSM."""
        return self.data

    async def update_data(self, **kwargs) -> None:
        """Сохраняет данные FSM."""
        self.data.update(kwargs)

    async def get_state(self) -> str:
        """Возвращает активное состояние."""
        return self.state_name

    async def set_state(self, state_name: str) -> None:
        """Устанавливает новое состояние."""
        self.state_name = state_name


def _draft() -> TrainingDraft:
    """Создает минимальный корректный draft меню тренировки."""
    draft = TrainingDraft(
        training=TrainingDraftData(training_id=None, training_date="2026-09-18")
    )
    draft.ui.message_id = 41
    return draft


def test_renderer_builds_resume_prompt_from_draft() -> None:
    """Экран восстановления строится из draft без FSMContext."""
    draft = _draft()
    view = render_training_view(draft, TrainingFlowStep.RESUME_PROMPT)

    assert "незавершённая тренировка" in view.text
    assert view.reply_markup is not None


def test_renderer_builds_calendar_with_contextual_back_button() -> None:
    """Проверяет календарь и кнопку выхода для создания и редактирования."""
    draft = _draft()
    draft.ui.calendar_year = 2026
    draft.ui.calendar_month = 9
    draft.suggestions.training_dates = ["2026-09-18"]

    creation_view = render_training_view(draft, TrainingFlowStep.SELECT_DATE)
    creation_labels = [
        button.text for row in creation_view.reply_markup.inline_keyboard for button in row
    ]

    draft.selection.mode = TrainingMode.EDIT_DATE.value
    editing_view = render_training_view(draft, TrainingFlowStep.SELECT_DATE)
    editing_labels = [
        button.text for row in editing_view.reply_markup.inline_keyboard for button in row
    ]

    assert "✓18" in creation_labels
    assert "❌ Отменить" in creation_labels
    assert "✎18" in editing_labels
    assert "← К редактированию" in editing_labels


def test_renderer_builds_months_and_years_calendar_views() -> None:
    """Renderer допускает представления календаря, для которых месяц не нужен."""
    draft = _draft()
    draft.ui.calendar_year = 2026
    draft.ui.calendar_month = None

    draft.ui.calendar_view = TrainingCalendarView.MONTHS
    months_view = render_training_view(draft, TrainingFlowStep.SELECT_DATE)
    months_labels = [
        button.text for row in months_view.reply_markup.inline_keyboard for button in row
    ]

    draft.ui.calendar_view = TrainingCalendarView.YEARS
    draft.ui.calendar_year = 2025
    years_view = render_training_view(draft, TrainingFlowStep.SELECT_DATE)
    years_labels = [
        button.text for row in years_view.reply_markup.inline_keyboard for button in row
    ]

    assert "Янв" in months_labels
    assert "2025" in years_labels


async def test_transition_recovers_current_screen_without_applying_change() -> None:
    """Удаленный UI восстанавливается, а предполагаемый draft не сохраняется."""
    current_draft = _draft()
    next_draft = deepcopy(current_draft)
    next_draft.training.comment = "Не должен сохраниться"
    state = FakeFSMContext(current_draft, TrainingStates.menu.state)
    bot = SimpleNamespace(
        edit_message_text=AsyncMock(
            side_effect=TelegramBadRequest(
                method=EditMessageText(chat_id=1, message_id=41, text="test"),
                message="Bad Request: message to edit not found",
            )
        ),
        send_message=AsyncMock(return_value=SimpleNamespace(message_id=77)),
    )

    result = await transition_training_screen(
        bot=bot,
        chat_id=1,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.MENU,
    )

    assert result is TrainingTransitionResult.RECOVERED
    assert current_draft.training.comment is None
    assert current_draft.ui.message_id == 77
    assert state.state_name == TrainingStates.menu.state
    assert state.data["training_draft"]["training"]["comment"] is None


async def test_transition_accepts_message_not_modified() -> None:
    """Telegram-ответ message is not modified не отменяет переход."""
    current_draft = _draft()
    next_draft = deepcopy(current_draft)
    next_draft.training.comment = "Новый комментарий"
    state = FakeFSMContext(current_draft, TrainingStates.menu.state)
    bot = SimpleNamespace(
        edit_message_text=AsyncMock(
            side_effect=TelegramBadRequest(
                method=EditMessageText(chat_id=1, message_id=41, text="test"),
                message="Bad Request: message is not modified",
            )
        ),
        send_message=AsyncMock(),
    )

    result = await transition_training_screen(
        bot=bot,
        chat_id=1,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.MENU,
    )

    assert result is TrainingTransitionResult.APPLIED
    assert state.data["training_draft"]["training"]["comment"] == "Новый комментарий"


async def test_show_or_recover_target_replaces_message_for_resume_prompt() -> None:
    """Проверяет принудительную замену UI при повторном запуске тренировки."""
    draft = _draft()
    state = FakeFSMContext(draft, TrainingStates.menu.state)
    bot = SimpleNamespace(
        send_message=AsyncMock(return_value=SimpleNamespace(message_id=77)),
        delete_message=AsyncMock(),
    )

    await show_or_recover_target(
        bot=bot,
        chat_id=1,
        state=state,
        draft=draft,
        step=TrainingFlowStep.RESUME_PROMPT,
    )

    assert draft.ui.message_id == 77
    assert state.state_name == TrainingStates.resume_prompt.state
    assert "незавершённая тренировка" in bot.send_message.await_args.kwargs["text"]
    bot.delete_message.assert_awaited_once_with(chat_id=1, message_id=41)


async def test_replace_after_backend_restores_result_after_message_deletion() -> None:
    """Проверяет создание экрана фактического результата после backend-операции."""
    draft = _draft()
    draft.training.training_id = 10
    state = FakeFSMContext(draft, TrainingStates.add_comment.state)
    bot = SimpleNamespace(
        edit_message_text=AsyncMock(
            side_effect=TelegramBadRequest(
                method=EditMessageText(chat_id=1, message_id=41, text="test"),
                message="Bad Request: message to edit not found",
            )
        ),
        send_message=AsyncMock(return_value=SimpleNamespace(message_id=77)),
    )

    await replace_after_backend(
        bot=bot,
        chat_id=1,
        state=state,
        draft=draft,
        step=TrainingFlowStep.RESULT,
    )

    assert draft.ui.message_id == 77
    assert state.state_name == TrainingStates.result.state
    bot.send_message.assert_awaited_once()
