"""Построение Telegram-экранов тренировки без побочных эффектов."""

from dataclasses import dataclass
from datetime import date, datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.formatters.training import format_training_step
from app.bot.fsm.training import (
    TrainingCalendarView,
    TrainingDraft,
    TrainingFlowStep,
    TrainingMode,
    check_accept_addition_for_draft,
    get_draft_exercise,
    get_weight_repetitions_modes_values_from_draft,
    has_draft_exercises,
)
from app.bot.fsm.training.states import (
    accept_button_by_mode,
    exercise_button_by_mode,
    weight_back_button_by_mode,
)
from app.bot.keyboards.training_kb import (
    get_ikb_accept_addition,
    get_ikb_changed_date,
    get_ikb_edit_menu,
    get_ikb_edit_select_exercise_fab,
    get_ikb_edit_select_set_fab,
    get_ikb_finish_add_comment,
    get_ikb_open_inline_search,
    get_ikb_select_exercise_fab,
    get_ikb_training_menu,
    ikb_edit_accept_delete,
)

from .calendar import render_training_calendar


@dataclass(frozen=True, slots=True)
class TrainingView:
    """Готовое представление одного главного сообщения тренировки."""

    text: str
    reply_markup: InlineKeyboardMarkup | None


def render_training_view(draft: TrainingDraft, step: TrainingFlowStep) -> TrainingView:
    """Строит главный экран тренировки из draft и логического шага."""
    return TrainingView(
        text=format_training_step(draft, step),
        reply_markup=_render_keyboard(draft, step),
    )


def _render_keyboard(
    draft: TrainingDraft,
    step: TrainingFlowStep,
) -> InlineKeyboardMarkup | None:
    """Возвращает клавиатуру конкретного шага без изменения draft."""
    if step is TrainingFlowStep.SELECT_DATE:
        return _calendar_keyboard(draft)
    if step is TrainingFlowStep.CHANGE_DATE_ACCEPT:
        conflict = draft.ui.date_conflict
        if conflict is None or conflict.training.training_date is None:
            raise ValueError("Для подтверждения смены даты нужен date_conflict")
        return get_ikb_changed_date(date.fromisoformat(conflict.training.training_date))
    if step is TrainingFlowStep.MENU:
        return _menu_keyboard(draft)
    if step is TrainingFlowStep.SELECT_EXERCISE:
        return get_ikb_select_exercise_fab(
            exercise_data=draft.suggestions.most_frequent_exercises,
            page=draft.ui.exercise_page,
            has_next_button=draft.selection.exercise_id is not None,
            has_accept_addition_button=check_accept_addition_for_draft(draft),
            selected_exercise_id=draft.selection.exercise_id or draft.ui.current_exercise_id,
        )
    if step is TrainingFlowStep.SELECT_WEIGHT:
        return _value_keyboard(draft, is_weight=True)
    if step is TrainingFlowStep.SELECT_REPETITIONS:
        return _value_keyboard(draft, is_weight=False)
    if step is TrainingFlowStep.SELECT_SETS_COUNT:
        mode = _mode(draft)
        accept_button = accept_button_by_mode[mode]
        return get_ikb_open_inline_search(
            entity_name="кол-во подходов",
            back_button_text="Повторения",
            back_button_callback_data="to_repetitions",
            has_accept_button=check_accept_addition_for_draft(draft),
            accept_button_text=accept_button.text,
            accept_button_callback_data=accept_button.callback_data,
            has_delete_set_button=mode is TrainingMode.EDIT_SET,
        )
    if step is TrainingFlowStep.ACCEPT_ADDITION:
        return get_ikb_accept_addition(_mode(draft))
    if step is TrainingFlowStep.ADD_COMMENT:
        return get_ikb_finish_add_comment(current_comment=draft.training.comment)
    if step is TrainingFlowStep.EDIT_MENU:
        return get_ikb_edit_menu(has_edit_exercise_button=has_draft_exercises(draft))
    if step is TrainingFlowStep.EDIT_SELECT_EXERCISE:
        return get_ikb_edit_select_exercise_fab(
            draft.training.exercises,
            page=draft.ui.edit_exercise_page,
        )
    if step is TrainingFlowStep.EDIT_SELECT_SET:
        exercise = get_draft_exercise(draft, draft.edit.exercise_id)
        return get_ikb_edit_select_set_fab(exercise.sets, page=draft.ui.edit_set_page)
    if step is TrainingFlowStep.EDIT_DELETE:
        return ikb_edit_accept_delete
    if step is TrainingFlowStep.RESUME_PROMPT:
        from app.bot.keyboards.training_kb.ikb_resume_prompt import get_ikb_resume_prompt

        return get_ikb_resume_prompt()
    if step is TrainingFlowStep.RESULT:
        return None
    raise ValueError(f"Неподдерживаемый шаг тренировки: {step}")


def _menu_keyboard(draft: TrainingDraft) -> InlineKeyboardMarkup:
    """Собирает клавиатуру главного меню тренировки."""
    last_weight = str(draft.ui.last_weight or "").rstrip("0").rstrip(".")
    last_repetitions = draft.ui.last_repetitions or ""
    return get_ikb_training_menu(
        is_add_edit_button=has_draft_exercises(draft),
        is_add_add_set_button=draft.ui.current_exercise_id is not None,
        repeat_set_button_text=f"{last_weight}×{last_repetitions}",
    )


def _calendar_keyboard(draft: TrainingDraft) -> InlineKeyboardMarkup:
    """Строит календарь с кнопкой выхода для текущего режима тренировки."""
    year = draft.ui.calendar_year
    month = draft.ui.calendar_month
    calendar_view = draft.ui.calendar_view or TrainingCalendarView.DAYS
    if year is None or (calendar_view is TrainingCalendarView.DAYS and month is None):
        raise ValueError("Для календаря должны быть сохранены параметры текущего представления")

    if draft.selection.mode is TrainingMode.EDIT_DATE.value:
        back_button = InlineKeyboardButton(
            text="← К редактированию",
            callback_data="to_edit_menu",
        )
    else:
        back_button = InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")

    return render_training_calendar(
        view=calendar_view,
        year=year,
        month=month,
        training_dates=[date.fromisoformat(item) for item in draft.suggestions.training_dates],
        editing_date=_editing_date(draft),
        back_button=back_button,
    )


def _editing_date(draft: TrainingDraft) -> date | None:
    """Возвращает текущую дату тренировки только для режима ее редактирования."""
    if draft.selection.mode is not TrainingMode.EDIT_DATE.value:
        return None

    training_date = draft.training.training_date
    if training_date is None:
        return None
    if isinstance(training_date, datetime):
        return training_date.date()
    if isinstance(training_date, date):
        return training_date
    return date.fromisoformat(training_date)


def _value_keyboard(draft: TrainingDraft, *, is_weight: bool) -> InlineKeyboardMarkup:
    """Собирает клавиатуру ввода веса или повторений."""
    mode = _mode(draft)
    accept_button = accept_button_by_mode[mode]
    if is_weight:
        back_button = weight_back_button_by_mode[mode]
        return get_ikb_open_inline_search(
            entity_name="вес",
            back_button_text=back_button.text,
            back_button_callback_data=back_button.callback_data,
            has_next_button=draft.selection.weight is not None,
            next_button_text="Повторения",
            next_button_callback_data="to_repetitions",
            has_accept_button=check_accept_addition_for_draft(draft),
            accept_button_text=accept_button.text,
            accept_button_callback_data=accept_button.callback_data,
            has_delete_set_button=mode is TrainingMode.EDIT_SET,
            switch_inline_query=get_weight_repetitions_modes_values_from_draft(
                draft, is_weight=True
            ),
        )
    back_button = exercise_button_by_mode.get(mode)
    return get_ikb_open_inline_search(
        entity_name="повторения",
        back_button_text="Вес",
        back_button_callback_data="to_weight",
        has_next_button=(
            draft.selection.repetitions is not None and mode is not TrainingMode.EDIT_SET
        ),
        next_button_text="Кол-во подходов",
        next_button_callback_data="to_sets_count",
        has_accept_button=check_accept_addition_for_draft(draft),
        accept_button_text=accept_button.text,
        accept_button_callback_data=accept_button.callback_data,
        has_delete_set_button=mode is TrainingMode.EDIT_SET,
        switch_inline_query=get_weight_repetitions_modes_values_from_draft(
            draft, is_repetitions=True
        ),
    )


def _mode(draft: TrainingDraft) -> TrainingMode:
    """Возвращает режим ввода, обязательный для экранов выбора значения."""
    if draft.selection.mode is None:
        raise ValueError("Для экрана ввода не задан режим тренировки")
    return TrainingMode(draft.selection.mode)
