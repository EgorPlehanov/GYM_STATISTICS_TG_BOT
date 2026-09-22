"""Тесты обработки конфликтов при изменении даты тренировки."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.bot.api_client.schemas.trainings import (
    BotTrainingSaveOutcome,
    BotTrainingSaveResult,
)
from app.bot.fsm.training import (
    TrainingDateConflict,
    TrainingDraft,
    TrainingDraftData,
    draft_to_json,
)
from app.bot.handlers.training_units import date as date_handlers


class FakeFSMContext:
    """Минимальный FSMContext для обработчика изменения даты."""

    def __init__(self, draft: TrainingDraft) -> None:
        """Сохраняет исходный draft в JSON-friendly виде."""
        self.data = {"training_draft": draft_to_json(draft)}

    async def get_data(self) -> dict:
        """Возвращает данные FSM."""
        return self.data


async def test_replace_conflict_keeps_database_unchanged_until_finish(monkeypatch) -> None:
    """Выбор замены сохраняет намерение в draft без удаления тренировки из БД."""
    source_training_id = 10
    conflict_training_id = 20
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=source_training_id,
            training_date="2026-09-01",
        )
    )
    draft.ui.message_id = 42
    draft.ui.date_conflict = TrainingDateConflict(
        training=TrainingDraftData(
            training_id=conflict_training_id,
            training_date="2026-09-02",
        )
    )
    state = FakeFSMContext(draft)
    callback = SimpleNamespace(
        message=SimpleNamespace(message_id=42, chat=SimpleNamespace(id=1)),
        bot=object(),
        answer=AsyncMock(),
    )
    captured = {}

    async def fake_replace_after_backend(**kwargs) -> None:
        """Сохраняет draft, который был бы показан после backend-операции."""
        captured.update(kwargs)

    monkeypatch.setattr(date_handlers, "replace_after_backend", fake_replace_after_backend)

    await date_handlers.changed_to_current_date(callback, state)

    next_draft = captured["draft"]
    assert next_draft.training.training_id == source_training_id
    assert next_draft.training.training_date == "2026-09-02"
    assert next_draft.edit.replace_training_id == conflict_training_id
    assert next_draft.ui.date_conflict is None


async def test_opening_date_calendar_keeps_pending_training_replacement(monkeypatch) -> None:
    """Повторное изменение даты не отменяет уже выбранную замену."""
    draft = TrainingDraft(
        training=TrainingDraftData(training_id=10, training_date="2026-09-02")
    )
    draft.ui.message_id = 42
    draft.edit.replace_training_id = 20
    state = FakeFSMContext(draft)
    callback = SimpleNamespace(
        message=SimpleNamespace(message_id=42, chat=SimpleNamespace(id=1)),
        bot=object(),
        answer=AsyncMock(),
    )
    captured = {}

    async def fake_transition_training_screen(**kwargs) -> None:
        """Запоминает draft, переданный на следующий экран."""
        captured.update(kwargs)

    monkeypatch.setattr(
        date_handlers,
        "transition_training_screen",
        fake_transition_training_screen,
    )

    await date_handlers.open_edit_date(callback, state)

    assert captured["next_draft"].edit.replace_training_id == 20


async def test_save_and_go_keeps_pending_replacement(monkeypatch) -> None:
    """Сохранение перед переходом завершает предыдущую отложенную замену."""
    source_training_id = 10
    replaced_training_id = 20
    next_conflict_id = 30
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=source_training_id,
            training_date="2026-09-02",
        )
    )
    draft.ui.message_id = 42
    draft.edit.replace_training_id = replaced_training_id
    draft.ui.date_conflict = TrainingDateConflict(
        training=TrainingDraftData(
            training_id=next_conflict_id,
            training_date="2026-09-03",
        )
    )
    state = FakeFSMContext(draft)
    callback = SimpleNamespace(
        from_user=SimpleNamespace(id=1),
        message=SimpleNamespace(message_id=42, chat=SimpleNamespace(id=1)),
        bot=object(),
        answer=AsyncMock(),
    )
    api_client = SimpleNamespace(
        save_training=AsyncMock(
            return_value=BotTrainingSaveResult(
                training_id=source_training_id,
                outcome=BotTrainingSaveOutcome.UPDATED,
                training_dates=[date(2026, 9, 2)],
            )
        )
    )
    captured = {}

    class FakeBotApiClient:
        """Контекстный клиент API без сетевого запроса."""

        async def __aenter__(self):
            """Возвращает подготовленный клиент."""
            return api_client

        async def __aexit__(self, *_args):
            """Не подавляет исключения теста."""
            return False

    async def fake_replace_after_backend(**kwargs) -> None:
        """Запоминает итоговый draft после сохранения."""
        captured.update(kwargs)

    monkeypatch.setattr(date_handlers, "BotApiClient", FakeBotApiClient)
    monkeypatch.setattr(date_handlers, "replace_after_backend", fake_replace_after_backend)

    await date_handlers.save_current_training_and_open_selected_date(callback, state)

    save_kwargs = api_client.save_training.await_args.kwargs
    assert save_kwargs["replace_training_id"] == replaced_training_id
    assert save_kwargs["training"].training_id == source_training_id
    assert save_kwargs["training"].training_date == date(2026, 9, 2)
    assert captured["draft"].training.training_id == next_conflict_id
