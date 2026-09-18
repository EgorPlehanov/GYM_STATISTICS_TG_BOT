"""Тесты renderer-а и восстановления главного сообщения тренировки."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import EditMessageText

from app.bot.fsm.training import (
    TrainingDraft,
    TrainingDraftData,
    TrainingFlowStep,
    TrainingStates,
    draft_to_json,
)
from app.bot.training_ui import (
    TrainingTransitionResult,
    render_training_view,
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
