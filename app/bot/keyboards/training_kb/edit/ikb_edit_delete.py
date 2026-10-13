"""Клавиатуры выбора целей удаления из черновика тренировки."""

import math

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.formatters.training import format_draft_set_to_text
from app.bot.fsm.training.draft import TrainingDraftExercise


class EditDeleteExerciseCallback(CallbackData, prefix="ed_del_ex"):
    """Действие с упражнением на экране выбора удаления."""

    action: str
    page: int
    exercise_id: int


class EditDeleteSetCallback(CallbackData, prefix="ed_del_set"):
    """Действие с подходом на экране выбора удаления."""

    action: str
    page: int
    local_id: str


def get_ikb_edit_delete_exercises(
    exercises: list[TrainingDraftExercise],
    *,
    selected_set_local_ids: set[str],
    page: int,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    """Создает экран выбора упражнений и перехода к их подходам."""
    builder = InlineKeyboardBuilder()
    all_set_local_ids = {
        set_data.local_id
        for exercise in exercises
        for set_data in exercise.sets
    }
    all_selected = bool(all_set_local_ids) and all_set_local_ids <= selected_set_local_ids
    builder.row(
        InlineKeyboardButton(
            text="☑ Снять выбор со всех" if all_selected else "☐ Выбрать все",
            callback_data=EditDeleteExerciseCallback(
                action="toggle_all", page=page, exercise_id=0
            ).pack(),
        )
    )
    for exercise in exercises[page * page_size:(page + 1) * page_size]:
        selected_count = sum(
            set_data.local_id in selected_set_local_ids for set_data in exercise.sets
        )
        if selected_count == len(exercise.sets):
            label = f"☑ {exercise.exercise_name}"
        elif selected_count:
            label = f"{selected_count}/{len(exercise.sets)} {exercise.exercise_name}"
        else:
            label = f"☐ {exercise.exercise_name}"
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=EditDeleteExerciseCallback(
                    action="toggle", page=page, exercise_id=exercise.exercise_id
                ).pack(),
            ),
            InlineKeyboardButton(
                text=f"{len(exercise.sets)} подходов →",
                callback_data=EditDeleteExerciseCallback(
                    action="open", page=page, exercise_id=exercise.exercise_id
                ).pack(),
            ),
        )
    _add_exercise_pagination(builder, exercises, page, page_size)
    _add_delete_actions(builder, selected_set_local_ids, back_callback_data="delete_back")
    return builder.as_markup()


def get_ikb_edit_delete_sets(
    exercise: TrainingDraftExercise,
    *,
    selected_set_local_ids: set[str],
    page: int,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    """Создает экран выбора отдельных подходов упражнения.

    Args:
        exercise: упражнение, подходы которого отображаются.
        selected_set_local_ids: local_id подходов, отмеченных для удаления.
        page: текущая страница списка.
        page_size: количество подходов на странице.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=exercise.exercise_name,
            callback_data="delete_back_to_exercises",
        )
    )
    page_start = page * page_size
    page_sets = exercise.sets[page_start:(page + 1) * page_size]
    for local_set_number, set_data in enumerate(page_sets, start=page_start + 1):
        marker = "☑" if set_data.local_id in selected_set_local_ids else "☐"
        builder.row(
            InlineKeyboardButton(
                text=(
                    f"{marker} {local_set_number} · "
                    f"{format_draft_set_to_text(set_data, include_set_number=False)}"
                ),
                callback_data=EditDeleteSetCallback(
                    action="toggle", page=page, local_id=set_data.local_id
                ).pack(),
            )
        )
    _add_set_pagination(builder, exercise, page, page_size)
    _add_delete_actions(
        builder,
        selected_set_local_ids,
        back_callback_data="delete_back_to_exercises",
    )
    return builder.as_markup()


def get_ikb_edit_delete_confirm() -> InlineKeyboardMarkup:
    """Создает клавиатуру окончательного подтверждения удаления."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Отмена", callback_data="delete_confirm_cancel"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data="delete_apply"),
    )
    return builder.as_markup()


def _add_exercise_pagination(
    builder: InlineKeyboardBuilder,
    exercises: list[TrainingDraftExercise],
    page: int,
    page_size: int,
) -> None:
    """Добавляет символические стрелки пагинации упражнений."""
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(
            text="←", callback_data=EditDeleteExerciseCallback(
                action="prev", page=page, exercise_id=0
            ).pack()
        ))
    if page < math.ceil(len(exercises) / page_size) - 1:
        buttons.append(InlineKeyboardButton(
            text="→", callback_data=EditDeleteExerciseCallback(
                action="next", page=page, exercise_id=0
            ).pack()
        ))
    if buttons:
        builder.row(*buttons)


def _add_set_pagination(
    builder: InlineKeyboardBuilder,
    exercise: TrainingDraftExercise,
    page: int,
    page_size: int,
) -> None:
    """Добавляет символические стрелки пагинации подходов."""
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(
            text="←", callback_data=EditDeleteSetCallback(
                action="prev", page=page, local_id="0"
            ).pack()
        ))
    if page < math.ceil(len(exercise.sets) / page_size) - 1:
        buttons.append(InlineKeyboardButton(
            text="→", callback_data=EditDeleteSetCallback(
                action="next", page=page, local_id="0"
            ).pack()
        ))
    if buttons:
        builder.row(*buttons)


def _add_delete_actions(
    builder: InlineKeyboardBuilder,
    selected_set_local_ids: set[str],
    *,
    back_callback_data: str,
) -> None:
    """Добавляет возврат и доступное только при выборе подтверждение удаления."""
    actions = [InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback_data)]
    if selected_set_local_ids:
        actions.append(InlineKeyboardButton(text="🗑️ Удалить", callback_data="delete_confirm"))
    builder.row(*actions)
