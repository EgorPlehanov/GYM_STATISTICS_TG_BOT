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
    can_submit_set_form_for_draft,
    get_draft_exercise,
    has_draft_exercises,
)
from app.bot.keyboards.training_kb import (
    get_ikb_add_set_form,
    get_ikb_changed_date,
    get_ikb_edit_menu,
    get_ikb_edit_select_exercise_fab,
    get_ikb_edit_select_set_fab,
    get_ikb_finish_add_comment,
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
        return_to_form = (
            draft.ui.exercise_selection_return_step
            is TrainingFlowStep.ADD_SET_FORM
        )
        return get_ikb_select_exercise_fab(
            exercise_data=draft.suggestions.most_frequent_exercises,
            page=draft.ui.exercise_page,
            selected_exercise_id=draft.selection.exercise_id or draft.ui.current_exercise_id,
            back_button_callback_data=(
                "form_cancel_exercise_selection" if return_to_form else "to_menu"
            ),
            back_button_text="⬅️ К форме" if return_to_form else "⬅️ Меню",
        )
    if step is TrainingFlowStep.ADD_SET_FORM:
        is_editing = _mode(draft) is TrainingMode.EDIT_SET
        return get_ikb_add_set_form(
            exercise_name=draft.selection.exercise_name,
            weight=draft.selection.weight,
            repetitions=draft.selection.repetitions,
            sets_count=draft.selection.sets_count,
            can_submit=can_submit_set_form_for_draft(draft),
            is_editing=is_editing,
        )
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
    last_weight = _format_weight(draft.ui.last_weight)
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
            text="⬅️ К редактированию",
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
        vacated_date=(
            date.fromisoformat(draft.edit.original_training_date)
            if draft.edit.original_training_date is not None
            else None
        ),
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


def _mode(draft: TrainingDraft) -> TrainingMode:
    """Возвращает режим ввода, обязательный для экранов выбора значения."""
    if draft.selection.mode is None:
        raise ValueError("Для экрана ввода не задан режим тренировки")
    return TrainingMode(draft.selection.mode)


def _format_weight(weight: object | None) -> str:
    """Форматирует последний вес для кнопки повтора без незначащих нулей."""
    if weight is None:
        return ""
    from app.core.weights import format_weight

    return format_weight(weight)
