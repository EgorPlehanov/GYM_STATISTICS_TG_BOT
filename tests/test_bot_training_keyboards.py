"""Тесты клавиатур сценария тренировки."""

from app.bot.fsm.training import TrainingDraftExercise, TrainingDraftSet
from app.bot.keyboards.training_kb.edit.ikb_edit_delete import (
    get_ikb_edit_delete_exercises,
    get_ikb_edit_delete_sets,
)
from app.bot.keyboards.training_kb.edit.ikb_edit_select_exercise import (
    get_ikb_edit_select_exercise_fab,
)
from app.bot.keyboards.training_kb.edit.ikb_edit_select_set import (
    get_ikb_edit_select_set_fab,
)


def test_delete_set_keyboard_uses_local_numbers() -> None:
    """Проверяет локальную нумерацию подходов внутри упражнения."""
    exercise = TrainingDraftExercise(
        exercise_id=2,
        exercise_name="Присед",
        sets=[
            TrainingDraftSet(set_id=3, set_number=3, weight=80, repetitions=8),
            TrainingDraftSet(set_id=4, set_number=4, weight=85, repetitions=6),
        ],
    )

    keyboard = get_ikb_edit_delete_sets(
        exercise,
        selected_set_local_ids=set(),
        page=0,
    )

    assert keyboard.inline_keyboard[0][0].text == "Присед"
    assert keyboard.inline_keyboard[0][0].callback_data == "delete_back_to_exercises"
    assert keyboard.inline_keyboard[1][0].text.startswith("☐ 1 · ")
    assert keyboard.inline_keyboard[2][0].text.startswith("☐ 2 · ")
    assert keyboard.inline_keyboard[-1][0].callback_data == "delete_back_to_exercises"


def test_delete_exercises_keyboard_toggles_all_sets() -> None:
    """Проверяет кнопку выбора и снятия выбора всех подходов тренировки."""
    exercise = TrainingDraftExercise(
        exercise_id=2,
        exercise_name="Присед",
        sets=[TrainingDraftSet(set_id=3, set_number=3, weight=80, repetitions=8)],
    )

    unchecked = get_ikb_edit_delete_exercises(
        [exercise], selected_set_local_ids=set(), page=0
    )
    checked = get_ikb_edit_delete_exercises(
        [exercise], selected_set_local_ids={exercise.sets[0].local_id}, page=0
    )

    assert unchecked.inline_keyboard[0][0].text == "☐ Выбрать все"
    assert checked.inline_keyboard[0][0].text == "☑ Снять выбор со всех"


def test_edit_set_keyboard_uses_middle_dot_after_number() -> None:
    """Проверяет единый разделитель номера подхода на кнопке редактирования."""
    keyboard = get_ikb_edit_select_set_fab(
        [TrainingDraftSet(set_id=1, set_number=3, weight=80, repetitions=8)],
        exercise_name="Присед",
    )

    assert keyboard.inline_keyboard[1][0].text.startswith("1 · ")


def test_edit_exercise_keyboard_has_delete_all_action() -> None:
    """Выбор упражнений редактора предлагает переход к массовому удалению."""
    keyboard = get_ikb_edit_select_exercise_fab(
        [TrainingDraftExercise(exercise_id=1, exercise_name="Жим лежа")]
    )

    assert keyboard.inline_keyboard[-1][0].text == "🗑️ Удалить все упражнения"
    assert keyboard.inline_keyboard[-1][0].callback_data == "delete_all_exercises"
