"""Тесты форматирования Telegram-текста тренировки."""

from app.bot.formatters.training import (
    format_exercises_data_from_draft,
    get_current_values_from_draft,
    get_training_values_from_draft,
    result_format_exercise_data_from_draft,
)
from app.bot.fsm.training import (
    TrainingDraft,
    TrainingDraftData,
    TrainingDraftExercise,
    TrainingDraftSet,
    TrainingMode,
)


def test_training_values_from_draft_formats_empty_training() -> None:
    """Проверяет форматирование даты и пустой тренировки."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=None,
            training_date="2026-09-13",
        )
    )

    text = get_training_values_from_draft(draft)

    assert "<b>Вс</b> <b>13.09.2026</b>" in text
    assert "Добавьте упражнения" in text


def test_format_exercises_data_from_draft_marks_edit_set() -> None:
    """Проверяет выделение редактируемого подхода."""
    draft = _build_training_draft()
    draft.edit.exercise_id = 1
    draft.edit.set_id = 1

    text = format_exercises_data_from_draft(draft)

    assert "✏️ ◼️ <b>Жим лежа</b>:" in text
    assert "✏️ \t▫️ 1) 18:30 - 80 × 8" in text


def test_training_values_from_draft_marks_delete_target() -> None:
    """Проверяет зачеркнутый текст при подтверждении удаления."""
    draft = _build_training_draft()
    draft.edit.exercise_id = 1

    text = get_training_values_from_draft(draft, delete_accept_flag=True)

    assert "<s><b>Жим лежа</b></s>" in text
    assert "<s>1) 18:30 - 80 × 8</s>" in text


def test_current_values_from_draft_formats_selection() -> None:
    """Проверяет текущий ввод из selection/edit draft."""
    draft = _build_training_draft()
    draft.selection.mode = TrainingMode.EDIT_SET.value
    draft.selection.sets_count = 2
    draft.selection.weight = 82.5
    draft.selection.repetitions = 6
    draft.edit.exercise_name = "Жим лежа"
    draft.edit.set_id = 1

    text = get_current_values_from_draft(draft)

    assert "Кол-во подходов" in text
    assert "<u>Жим лежа</u>" in text
    assert "<u>82.5</u>" in text
    assert "<u>6</u>" in text


def test_result_format_exercise_data_from_draft_groups_equal_sets() -> None:
    """Проверяет компактную группировку одинаковых подходов в результате."""
    draft = _build_training_draft(
        sets=[
            TrainingDraftSet(None, 1, 80.0, 8),
            TrainingDraftSet(None, 2, 80.0, 8),
            TrainingDraftSet(None, 3, 82.5, 6),
        ]
    )

    text = result_format_exercise_data_from_draft(draft)

    assert "80×8×2, 82.5×6" in text


def _build_training_draft(
    sets: list[TrainingDraftSet] | None = None,
) -> TrainingDraft:
    """Создает draft тренировки для тестов форматирования.

    Args:
        sets: подходы упражнения. Если не переданы, используется один подход.

    Returns:
        Заполненный `TrainingDraft` с одним упражнением.
    """
    return TrainingDraft(
        training=TrainingDraftData(
            training_id=10,
            training_date="2026-09-13",
            exercises=[
                TrainingDraftExercise(
                    exercise_id=1,
                    exercise_name="Жим лежа",
                    sets=sets
                    or [
                        TrainingDraftSet(
                            set_id=21,
                            set_number=1,
                            weight=80.0,
                            repetitions=8,
                            execution_time="2026-09-13T18:30:00",
                        )
                    ],
                )
            ],
        )
    )
