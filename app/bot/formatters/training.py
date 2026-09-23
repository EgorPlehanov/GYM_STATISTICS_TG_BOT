"""Форматирование текста Telegram-сценария тренировки."""

from datetime import date, datetime

from aiogram import html

from app.bot.fsm.training import (
    TrainingDraft,
    TrainingDraftSet,
    TrainingFlowStep,
    TrainingMode,
)

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def format_exercises_data_from_draft(
    draft: TrainingDraft,
    *,
    delete_accept_flag: bool = False,
) -> str:
    """Форматирует упражнения и подходы из `TrainingDraft`.

    Args:
        draft: текущий FSM draft тренировки.
        delete_accept_flag: выделить удаляемое упражнение или подход.

    Returns:
        HTML-текст списка упражнений и подходов для Telegram.
    """
    delete_all_accept_flag = (
        delete_accept_flag
        and draft.edit.exercise_id is None
        and draft.edit.set_id is None
    )

    text_parts = []
    for exercise in draft.training.exercises:
        exercise_edit_flag = (
            "✏️ "
            if draft.edit.exercise_id == exercise.exercise_id or delete_all_accept_flag
            else ""
        )
        exercise_name = html.bold(exercise.exercise_name)
        if (
            delete_accept_flag
            and draft.edit.exercise_id == exercise.exercise_id
            and (draft.edit.set_id is None or len(exercise.sets) == 1)
        ) or delete_all_accept_flag:
            exercise_name = html.strikethrough(exercise_name)

        exercise_text_parts = [f"{exercise_edit_flag}◼️ {exercise_name}:"]
        for local_set_number, set_data in enumerate(exercise.sets, start=1):
            set_edit_flag = ""
            if (
                draft.edit.exercise_id == exercise.exercise_id
                and (
                    draft.edit.set_id is None
                    or draft.edit.set_id == local_set_number
                )
                or delete_all_accept_flag
            ):
                set_edit_flag = "✏️ "

            set_text = (
                f"{local_set_number}) "
                f"{format_draft_set_to_text(set_data, include_set_number=False)}"
            )
            if (delete_accept_flag and set_edit_flag) or delete_all_accept_flag:
                set_text = html.strikethrough(set_text)

            exercise_text_parts.append(f"{set_edit_flag}\t▫️ {set_text}")

        text_parts.append(html.blockquote("\n".join(exercise_text_parts)))

    return "\n".join(text_parts)


def format_draft_set_to_text(
    set_data: TrainingDraftSet,
    *,
    set_id: int | None = None,
    include_set_number: bool = True,
) -> str:
    """Форматирует один подход из `TrainingDraft`.

    Args:
        set_data: данные подхода из draft.
        set_id: локальный номер подхода для отображения.
        include_set_number: добавить номер подхода в начало строки.

    Returns:
        Строка вида `1) 18:30 - 80 × 8`.
    """
    str_parts = []

    if include_set_number:
        str_parts.append(f"{set_id})")

    time = _format_time(set_data.execution_time)
    if time is not None:
        str_parts.append(f"{time} -")

    weight = _format_number(set_data.weight)
    if weight is not None:
        str_parts.append(weight)

    if set_data.repetitions is not None:
        str_parts.append(f"× {set_data.repetitions}")

    return " ".join(str_parts)


def result_format_exercise_sets_from_draft(sets_data: list[TrainingDraftSet]) -> str:
    """Форматирует подходы упражнения для итогового сообщения.

    Args:
        sets_data: список подходов упражнения.

    Returns:
        Компактная строка группировки одинаковых подходов.
    """
    sets = []
    factor = 0
    cur_weight = None
    cur_repetitions = None

    for set_data in sets_data:
        weight = _format_number(set_data.weight)
        repetitions = set_data.repetitions

        if cur_weight is None and cur_repetitions is None:
            cur_weight = weight
            cur_repetitions = repetitions

        if cur_weight != weight or cur_repetitions != repetitions:
            sets.append(_format_result_set(cur_weight, cur_repetitions, factor))
            factor = 0
            cur_weight = weight
            cur_repetitions = repetitions

        factor += 1
    else:
        sets.append(_format_result_set(cur_weight, cur_repetitions, factor))

    return ", ".join(sets)


def result_format_exercise_data_from_draft(draft: TrainingDraft) -> str:
    """Форматирует упражнения из draft для итогового сообщения."""
    text_parts = []
    for exercise in draft.training.exercises:
        exercise_text = html.blockquote(
            f"◼️ {exercise.exercise_name}:\n"
            "\t▫️ " + result_format_exercise_sets_from_draft(exercise.sets)
        )
        text_parts.append(exercise_text)

    return "\n".join(text_parts)


def get_training_values_from_draft(
    draft: TrainingDraft,
    *,
    is_result: bool = False,
    delete_accept_flag: bool = False,
) -> str | None:
    """Возвращает текст даты, комментария и упражнений из draft.

    Args:
        draft: текущий FSM draft тренировки.
        is_result: форматировать текст как итог сохраненной тренировки.
        delete_accept_flag: выделить удаляемую сущность.

    Returns:
        HTML-текст блока тренировки или None, если дата тренировки отсутствует.
    """
    training_date = _parse_date(draft.training.training_date)
    if training_date is None:
        return None

    date_edit_flag = (
        "✏️ " if _mode_from_value(draft.selection.mode) == TrainingMode.EDIT_DATE else ""
    )
    date_formatted = training_date.strftime("%d.%m.%Y")
    weekday_name = WEEKDAYS[training_date.weekday()]
    comment = ""
    if draft.training.comment:
        comment = f"\n{html.blockquote(html.italic(html.quote(draft.training.comment)))}"

    training_values = [
        f"{date_edit_flag}{html.bold(weekday_name)} "
        f"{html.bold(date_formatted)}{comment}"
    ]

    if is_result:
        training_values.append(
            f"{html.bold('Тренировка:')}\n{result_format_exercise_data_from_draft(draft)}"
        )
    elif draft.training.exercises:
        format_exercise_text = format_exercises_data_from_draft(
            draft,
            delete_accept_flag=delete_accept_flag,
        )
        training_values.append(f"{html.bold('Тренировка:')}\n{format_exercise_text}")
    else:
        training_values.append(
            f"{html.bold('Тренировка:')}\n{html.blockquote('❗Добавьте упражнения❗')}"
        )

    return "\n".join(training_values)


def get_current_values_from_draft(draft: TrainingDraft) -> str | None:
    """Возвращает текст текущего ввода из draft.

    Args:
        draft: текущий FSM draft тренировки.
    Returns:
        HTML-текст текущих значений или None, если текущих значений нет.
    """
    cur_values = []
    if draft.selection.sets_count is not None and draft.selection.sets_count > 1:
        cur_values.append(
            "🔁 Кол-во подходов: "
            f"x{html.bold(html.underline(draft.selection.sets_count))}"
        )

    exercise_name = draft.edit.exercise_name or draft.selection.exercise_name
    if exercise_name is not None:
        cur_values.append(f"🏋️‍♂️ Упражнение: {html.bold(html.underline(exercise_name))}")

    if draft.edit.set_id is not None:
        cur_values.append(f"🔢 Подход: {html.bold(html.underline(draft.edit.set_id))}")

    if draft.selection.weight is not None:
        cur_values.append(
            f"⚖️ Вес: {html.bold(html.underline(draft.selection.weight))} кг"
        )

    if draft.selection.repetitions is not None:
        cur_values.append(
            f"🔂 Повторения: {html.bold(html.underline(draft.selection.repetitions))}"
        )

    if cur_values:
        return "Текущие значения:\n" + html.blockquote("\n".join(cur_values))
    return None


def get_delete_object_text_from_draft(draft: TrainingDraft) -> str:
    """Возвращает текст удаляемой сущности из typed draft."""
    if draft.edit.exercise_id is None:
        return "Всех упражнений с подходами"
    if draft.edit.set_id is None:
        return f"Всех подходов упражнения {html.underline(draft.edit.exercise_name)}"
    return f"Подхода упражнения {html.underline(draft.edit.exercise_name)}"


def format_training_step(
    draft: TrainingDraft,
    step: TrainingFlowStep,
    *,
    is_result: bool = False,
) -> str:
    """Строит текст экрана тренировки без обращения к FSMContext.

    Args:
        draft: данные текущего сценария.
        step: шаг, для которого строится экран.
        is_result: отобразить сохраненную тренировку как итог.

    Returns:
        Готовый HTML-текст Telegram-сообщения.
    """
    if step is TrainingFlowStep.RESUME_PROMPT:
        return _format_resume_prompt(draft)

    text_parts: list[str] = []
    training_values = get_training_values_from_draft(
        draft,
        is_result=is_result or step is TrainingFlowStep.RESULT,
        delete_accept_flag=step is TrainingFlowStep.EDIT_DELETE,
    )
    if training_values is not None:
        text_parts.append(training_values)

    if step is TrainingFlowStep.RESULT:
        return "\n".join(text_parts)

    current_values = get_current_values_from_draft(draft)
    if current_values is not None:
        text_parts.append(current_values)

    text_parts.append(_get_step_text(draft, step))
    return "\n".join(text_parts)


def _get_step_text(draft: TrainingDraft, step: TrainingFlowStep) -> str:
    """Возвращает заголовок и дополнительный текст конкретного шага."""
    step_to_text = {
        TrainingFlowStep.SELECT_DATE: "Выберите дату",
        TrainingFlowStep.CHANGE_DATE_ACCEPT: "Что делать с этой тренировкой",
        TrainingFlowStep.SELECT_EXERCISE: "Выберите упражнение",
        TrainingFlowStep.SELECT_WEIGHT: "Выберите доп. вес",
        TrainingFlowStep.SELECT_REPETITIONS: "Выберите кол-во повторений",
        TrainingFlowStep.ACCEPT_ADDITION: "Подтвердите добавление",
        TrainingFlowStep.SELECT_SETS_COUNT: "Выберите кол-во добавляемых подходов",
        TrainingFlowStep.MENU: "Что дальше",
        TrainingFlowStep.ADD_COMMENT: "Отправить комментарий или просто заверши",
        TrainingFlowStep.EDIT_MENU: "Что исправить",
        TrainingFlowStep.EDIT_SELECT_EXERCISE: "Выберите упражнение",
        TrainingFlowStep.EDIT_SELECT_SET: "Выберите подход",
        TrainingFlowStep.EDIT_DELETE: "Подтвердите удаление",
    }
    additional_text = ""
    if step is TrainingFlowStep.EDIT_DELETE:
        additional_text = get_delete_object_text_from_draft(draft)
    elif step is TrainingFlowStep.CHANGE_DATE_ACCEPT and draft.ui.date_conflict:
        conflict_draft = TrainingDraft(training=draft.ui.date_conflict.training)
        additional_text = get_training_values_from_draft(conflict_draft, is_result=True) or ""

    if additional_text:
        additional_text = html.blockquote(
            f"\n❗❗❗\n{html.bold(additional_text)}\n❗❗❗"
        )
    date_hint = ""
    if step is TrainingFlowStep.SELECT_DATE and draft.edit.original_training_date:
        date_hint = "\n🗑 — дата освободится после сохранения"
    return (
        f"⬇️ {html.bold(html.underline(step_to_text[step]))} ⬇️"
        f"{additional_text}"
        f"{date_hint}"
    )


def _format_resume_prompt(draft: TrainingDraft) -> str:
    """Формирует краткое сообщение о незавершенном черновике."""
    training_date = _parse_date(draft.training.training_date)
    date_text = training_date.strftime("%d.%m.%Y") if training_date else "не выбрана"
    exercises_count = len(draft.training.exercises)
    sets_count = sum(len(exercise.sets) for exercise in draft.training.exercises)
    return (
        "Есть незавершённая тренировка.\n\n"
        f"Дата: {html.bold(date_text)}\n"
        f"Упражнений: {html.bold(exercises_count)}\n"
        f"Подходов: {html.bold(sets_count)}"
    )


def _format_result_set(weight: str | None, repetitions: int | None, factor: int) -> str:
    """Форматирует сгруппированный подход итогового сообщения."""
    return f"{weight}×{repetitions}{f'×{factor}' if factor > 1 else ''}"


def _format_number(value: float | int | None) -> str | None:
    """Форматирует число без лишних нулей после запятой."""
    if value is None:
        return None
    return str(value).rstrip("0").rstrip(".")


def _format_time(value: str | datetime | None) -> str | None:
    """Форматирует время подхода в HH:MM."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    return datetime.fromisoformat(value).strftime("%H:%M")


def _parse_date(value: date | datetime | str | None) -> date | None:
    """Возвращает date из значения draft."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _mode_from_value(value: str | TrainingMode | None) -> TrainingMode | None:
    """Возвращает TrainingMode из строки или старого enum."""
    if value is None or isinstance(value, TrainingMode):
        return value
    try:
        return TrainingMode(value)
    except ValueError:
        return None
