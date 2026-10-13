"""Тесты общих обработчиков сценария тренировки."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.bot.fsm.training import (
    TrainingDeletionContext,
    TrainingDeletionView,
    TrainingDraft,
    TrainingDraftData,
    TrainingDraftExercise,
    TrainingDraftSet,
    TrainingFlowStep,
    TrainingMode,
    draft_to_json,
)
from app.bot.handlers import training as training_handlers
from app.bot.handlers.training_units.edit import menu as edit_menu_handlers
from app.bot.keyboards.training_kb.edit.ikb_edit_delete import EditDeleteExerciseCallback


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


def _edit_draft() -> TrainingDraft:
    """Создает draft с выбранным подходом для тестов удаления."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=10,
            training_date="2026-10-03",
            exercises=[
                TrainingDraftExercise(
                    exercise_id=1,
                    exercise_name="Жим лежа",
                    sets=[
                        TrainingDraftSet(
                            set_id=11,
                            set_number=3,
                            weight=80,
                            repetitions=8,
                        )
                    ],
                )
            ],
        )
    )
    draft.ui.message_id = 42
    draft.edit.exercise_id = 1
    draft.edit.exercise_name = "Жим лежа"
    draft.edit.set_id = 1
    draft.edit.set_number = 1
    draft.selection.mode = TrainingMode.EDIT_SET.value
    draft.selection.exercise_id = 1
    draft.selection.exercise_name = "Жим лежа"
    draft.selection.weight = 82
    draft.selection.repetitions = 6
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


async def test_delete_set_remembers_edit_form_as_return_screen(monkeypatch) -> None:
    """Удаление подхода из формы помнит исходный экран без сброса параметров."""
    state = FakeFSMContext(_edit_draft())
    callback = SimpleNamespace(
        data="delete_set",
        bot=object(),
        message=SimpleNamespace(chat=SimpleNamespace(id=10)),
    )
    transition = AsyncMock()
    monkeypatch.setattr(
        edit_menu_handlers,
        "is_current_training_callback",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(edit_menu_handlers, "transition_training_screen", transition)

    await edit_menu_handlers.delete_accept(callback, state)

    next_draft = transition.await_args.kwargs["next_draft"]
    assert transition.await_args.kwargs["next_step"] is TrainingFlowStep.EDIT_DELETE
    assert next_draft.deletion.view is TrainingDeletionView.SETS
    assert next_draft.deletion.return_step is TrainingFlowStep.SET_FORM
    assert next_draft.selection.weight == 82
    assert next_draft.selection.repetitions == 6


async def test_delete_cancel_restores_saved_return_screen(monkeypatch) -> None:
    """Возврат из удаления восстанавливает форму редактирования подхода."""
    draft = _edit_draft()
    draft.deletion = TrainingDeletionContext(
        view=TrainingDeletionView.SETS,
        opened_exercise_id=1,
        return_step=TrainingFlowStep.SET_FORM,
    )
    state = FakeFSMContext(draft)
    callback = SimpleNamespace(
        bot=object(),
        message=SimpleNamespace(chat=SimpleNamespace(id=10)),
    )
    transition = AsyncMock()
    monkeypatch.setattr(
        edit_menu_handlers,
        "is_current_training_callback",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(edit_menu_handlers, "transition_training_screen", transition)

    await edit_menu_handlers.delete_cancel(callback, state)

    next_draft = transition.await_args.kwargs["next_draft"]
    assert transition.await_args.kwargs["next_step"] is TrainingFlowStep.SET_FORM
    assert next_draft.selection.weight == 82
    assert next_draft.selection.repetitions == 6
    assert next_draft.deletion.return_step is TrainingFlowStep.EDIT_MENU


async def test_delete_toggle_all_selects_all_draft_sets(monkeypatch) -> None:
    """Кнопка выбора всех целей отмечает подходы всех упражнений черновика."""
    draft = _edit_draft()
    draft.training.exercises.append(
        TrainingDraftExercise(
            exercise_id=2,
            exercise_name="Присед",
            sets=[TrainingDraftSet(set_id=12, set_number=4, weight=100, repetitions=5)],
        )
    )
    state = FakeFSMContext(draft)
    callback = SimpleNamespace(
        bot=object(),
        message=SimpleNamespace(chat=SimpleNamespace(id=10)),
    )
    transition = AsyncMock()
    monkeypatch.setattr(
        edit_menu_handlers,
        "is_current_training_callback",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(edit_menu_handlers, "transition_training_screen", transition)

    await edit_menu_handlers.change_delete_exercises(
        callback,
        EditDeleteExerciseCallback(action="toggle_all", page=0, exercise_id=0),
        state,
    )

    next_draft = transition.await_args.kwargs["next_draft"]
    expected_local_ids = {
        set_data.local_id
        for exercise in draft.training.exercises
        for set_data in exercise.sets
    }
    assert set(next_draft.deletion.selected_set_local_ids) == expected_local_ids


async def test_delete_all_exercises_preselects_all_sets(monkeypatch) -> None:
    """Массовое удаление из редактора выбирает все подходы черновика."""
    draft = _edit_draft()
    draft.training.exercises.append(
        TrainingDraftExercise(
            exercise_id=2,
            exercise_name="Присед",
            sets=[TrainingDraftSet(set_id=12, set_number=4, weight=100, repetitions=5)],
        )
    )
    state = FakeFSMContext(draft)
    callback = SimpleNamespace(
        data="delete_all_exercises",
        bot=object(),
        message=SimpleNamespace(chat=SimpleNamespace(id=10)),
    )
    transition = AsyncMock()
    monkeypatch.setattr(
        edit_menu_handlers,
        "is_current_training_callback",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(edit_menu_handlers, "transition_training_screen", transition)

    await edit_menu_handlers.delete_accept(callback, state)

    next_draft = transition.await_args.kwargs["next_draft"]
    assert transition.await_args.kwargs["next_step"] is TrainingFlowStep.EDIT_DELETE
    assert next_draft.deletion.return_step is TrainingFlowStep.EDIT_SELECT_EXERCISE
    assert set(next_draft.deletion.selected_set_local_ids) == {
        set_data.local_id
        for exercise in draft.training.exercises
        for set_data in exercise.sets
    }
