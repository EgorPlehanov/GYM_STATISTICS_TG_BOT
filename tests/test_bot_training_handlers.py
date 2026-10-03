"""Тесты общих обработчиков сценария тренировки."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.bot.fsm.training import TrainingDraft, TrainingDraftData, draft_to_json
from app.bot.handlers import training as training_handlers


class FakeFSMContext:
    """Минимальная реализация FSMContext для проверки отмены тренировки."""

    def __init__(self, draft: TrainingDraft) -> None:
        """Сохраняет черновик в формате, используемом FSM."""
        self.data = {"training_draft": draft_to_json(draft)}
        self.clear = AsyncMock()

    async def get_data(self) -> dict:
        """Возвращает сохраненные данные FSM."""
        return self.data


def _draft() -> TrainingDraft:
    """Создает минимальный черновик с контролируемым сообщением."""
    draft = TrainingDraft(
        training=TrainingDraftData(training_id=None, training_date="2026-10-03")
    )
    draft.ui.message_id = 42
    return draft


async def test_cancel_training_by_command_keeps_confirmation_message(monkeypatch) -> None:
    """Команда /cancel оставляет в чате наглядное подтверждение отмены."""
    state = FakeFSMContext(_draft())
    message = SimpleNamespace(
        bot=object(),
        chat=SimpleNamespace(id=10),
        answer=AsyncMock(),
        delete=AsyncMock(),
    )
    delete_training_message = AsyncMock()
    monkeypatch.setattr(
        training_handlers, "delete_training_message", delete_training_message
    )

    await training_handlers.cancel_training_by_command(message, state)

    state.clear.assert_awaited_once()
    delete_training_message.assert_awaited_once_with(
        bot=message.bot,
        chat_id=10,
        message_id=42,
    )
    message.answer.assert_awaited_once_with("❌ Тренировка отменена.")
    message.delete.assert_awaited_once()


async def test_cancel_training_by_callback_uses_ephemeral_notification(monkeypatch) -> None:
    """Кнопка отмены подтверждает действие всплывающим уведомлением."""
    state = FakeFSMContext(_draft())
    message = SimpleNamespace(chat=SimpleNamespace(id=10), answer=AsyncMock())
    callback = SimpleNamespace(bot=object(), message=message, answer=AsyncMock())
    delete_training_message = AsyncMock()
    monkeypatch.setattr(
        training_handlers, "is_current_training_callback", AsyncMock(return_value=True)
    )
    monkeypatch.setattr(
        training_handlers, "delete_training_message", delete_training_message
    )

    await training_handlers.cancel_training_by_callback(callback, state)

    state.clear.assert_awaited_once()
    delete_training_message.assert_awaited_once_with(
        bot=callback.bot,
        chat_id=10,
        message_id=42,
    )
    callback.answer.assert_awaited_once_with("❌ Тренировка отменена.")
    message.answer.assert_not_awaited()
