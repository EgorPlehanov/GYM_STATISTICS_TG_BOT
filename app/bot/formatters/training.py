"""Форматирование текста Telegram-сценария тренировки."""

from datetime import date, datetime
from typing import Any

from aiogram import html
from aiogram.fsm.context import FSMContext

from app.bot.fsm.training import (
    TrainingDraft,
    TrainingDraftSet,
    TrainingMode,
    TrainingStates,
    get_training_draft,
    legacy_exercise_data_to_draft,
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


def format_exercises_data(
    exercise_data: dict[str, int | dict],
    edit_exercise_id: int | None = None,
    edit_set_id: int | None = None,
    delete_accept_flag: bool = False,
) -> str:
    """Форматирует legacy `exercise_data` через временный draft adapter.

    Args:
        exercise_data: старый FSM-словарь тренировки.
        edit_exercise_id: id редактируемого упражнения.
        edit_set_id: локальный номер редактируемого подхода.
        delete_accept_flag: выделить удаляемую сущность.

    Returns:
        HTML-текст списка упражнений и подходов.
    """
    draft = legacy_exercise_data_to_draft(exercise_data)
    draft.edit.exercise_id = edit_exercise_id
    draft.edit.set_id = edit_set_id
    return format_exercises_data_from_draft(
        draft,
        delete_accept_flag=delete_accept_flag,
    )


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


def result_format_exercise_sets(sets_data: dict[str, dict[str, Any]]) -> str:
    """Форматирует legacy-подходы через временный draft adapter."""
    draft_sets = [
        TrainingDraftSet(
            set_id=set_data.get("id"),
            set_number=set_data["set_number"],
            weight=set_data["weight"],
            repetitions=set_data["repetitions"],
            execution_time=_normalize_datetime_or_none(set_data.get("time")),
        )
        for set_data in sets_data.values()
    ]
    return result_format_exercise_sets_from_draft(draft_sets)


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


def result_format_exercise_data(exercise_data: dict[str, int | dict]) -> str:
    """Форматирует legacy `exercise_data` для итогового сообщения."""
    return result_format_exercise_data_from_draft(
        legacy_exercise_data_to_draft(exercise_data)
    )


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


def get_training_values(
    user_data: dict[str, int | dict],
    is_result: bool = False,
) -> str | None:
    """Возвращает текст тренировки из legacy FSM data через draft adapter."""
    exercise_data = user_data.get("exercise_data")
    if exercise_data is None:
        return None

    draft = legacy_exercise_data_to_draft(exercise_data)
    draft.selection.mode = _mode_to_value(user_data.get("mode"))
    draft.edit.exercise_id = user_data.get("edit_exercise_id")
    draft.edit.set_id = user_data.get("edit_set_id")

    return get_training_values_from_draft(
        draft,
        is_result=is_result,
        delete_accept_flag=bool(user_data.get("delete_acept_flag")),
    )


def get_current_values_from_draft(
    draft: TrainingDraft,
    *,
    fallback_exercise_name: str | None = None,
) -> str | None:
    """Возвращает текст текущего ввода из draft.

    Args:
        draft: текущий FSM draft тренировки.
        fallback_exercise_name: последнее выбранное упражнение из legacy FSM,
            пока оно не перенесено в draft.

    Returns:
        HTML-текст текущих значений или None, если текущих значений нет.
    """
    cur_values = []
    if draft.selection.sets_count is not None and draft.selection.sets_count > 1:
        cur_values.append(
            "🔁 Кол-во подходов: "
            f"x{html.bold(html.underline(draft.selection.sets_count))}"
        )

    exercise_name = (
        draft.edit.exercise_name
        or draft.selection.exercise_name
        or fallback_exercise_name
    )
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


def get_current_values(user_data: dict[str, int | dict]) -> str | None:
    """Возвращает текст текущего ввода из legacy FSM data через draft adapter."""
    exercise_data = user_data.get("exercise_data")
    if exercise_data is None:
        return None

    draft = legacy_exercise_data_to_draft(exercise_data)
    draft.selection.mode = _mode_to_value(user_data.get("mode"))
    draft.selection.exercise_id = user_data.get("cur_exercise_id")
    draft.selection.exercise_name = user_data.get("cur_exercise_name")
    draft.selection.weight = user_data.get("weight")
    draft.selection.repetitions = user_data.get("repetitions")
    draft.selection.sets_count = user_data.get("sets_count")
    draft.edit.exercise_id = user_data.get("edit_exercise_id")
    draft.edit.exercise_name = user_data.get("edit_exercise_name")
    draft.edit.set_id = user_data.get("edit_set_id")

    return get_current_values_from_draft(
        draft,
        fallback_exercise_name=user_data.get("exercise_name"),
    )


async def get_delete_object_text(state: FSMContext) -> str:
    """Возвращает текст удаляемого объекта."""
    draft = await get_training_draft(state)

    if draft.edit.exercise_id is None:
        return "Всех упражнений с подходами"
    if draft.edit.set_id is None:
        return f"Всех подходов упражнения {html.underline(draft.edit.exercise_name)}"
    return f"Подхода упражнения {html.underline(draft.edit.exercise_name)}"


async def get_formatted_other_date(state: FSMContext) -> str:
    """Возвращает текст тренировки на другой выбранной дате."""
    user_data = await state.get_data()
    changed_exercise_data = user_data.get("changed_exercise_data")
    if changed_exercise_data is None:
        return ""

    changed_draft = legacy_exercise_data_to_draft(changed_exercise_data)
    return get_training_values_from_draft(changed_draft, is_result=True) or ""


async def get_state_text(state: FSMContext) -> str:
    """Возвращает текст текущего FSM-состояния."""
    state_to_text = {
        TrainingStates.select_date: "Выберите дату",
        TrainingStates.change_date_acept: "Что делать с этой тренировкой",
        TrainingStates.select_exercise: "Выберите упражнение",
        TrainingStates.select_weight: "Выберите доп. вес",
        TrainingStates.select_repetitions: "Выберите кол-во повторений",
        TrainingStates.acept_addition: "Подтвердите добавление",
        TrainingStates.select_sets_count: "Выберите кол-во добавляемых подходов",
        TrainingStates.menu: "Что дальше",
        TrainingStates.add_comment: "Отправить комментарий или просто заверши",
        TrainingStates.edit_menu: "Что исправить",
        TrainingStates.edit_select_exercise: "Выберите упражнение",
        TrainingStates.edit_select_set: "Выберите подход",
        TrainingStates.edit_delete: "Подтвердите удаление",
    }
    cur_state = await state.get_state()

    adition_text = ""
    if cur_state == TrainingStates.edit_delete:
        adition_text = await get_delete_object_text(state)
    elif cur_state == TrainingStates.change_date_acept:
        adition_text = await get_formatted_other_date(state)

    if adition_text:
        adition_text = html.blockquote(
            f"\n❗❗❗\n{html.bold(adition_text)}\n❗❗❗"
        )

    return f"⬇️ {html.bold(html.underline(state_to_text[cur_state]))} ⬇️" + adition_text


def serialize_datetime(obj: Any) -> str | None:
    """Сериализует datetime в ISO-строку для legacy-вызовов."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return None


async def get_formatted_state_date(state: FSMContext, is_result: bool = False) -> str:
    """Возвращает полный текст текущего состояния тренировки.

    Args:
        state: FSMContext текущего сценария тренировки.
        is_result: форматировать текст как итог сохраненной тренировки.

    Returns:
        HTML-текст, который отправляется или редактируется в Telegram.
    """
    user_data: dict[str, Any] = await state.get_data()
    text_list = []

    if user_data.get("exercise_data") is not None:
        draft = await get_training_draft(state)
        training_values = get_training_values_from_draft(
            draft,
            is_result=is_result,
            delete_accept_flag=bool(user_data.get("delete_acept_flag")),
        )
        if training_values is not None:
            text_list.append(training_values)

        if not is_result:
            cur_values = get_current_values_from_draft(
                draft,
                fallback_exercise_name=user_data.get("exercise_name"),
            )
            if cur_values is not None:
                text_list.append(cur_values)

    if not is_result:
        text_list.append(await get_state_text(state))

    return "\n".join(text_list)


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


def _normalize_datetime_or_none(value: datetime | str | None) -> str | None:
    """Возвращает datetime-значение в ISO-формате или None."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _mode_to_value(value: Any) -> str | None:
    """Возвращает строковое значение режима."""
    if value is None:
        return None
    if isinstance(value, TrainingMode):
        return value.value
    return str(value)


def _mode_from_value(value: str | TrainingMode | None) -> TrainingMode | None:
    """Возвращает TrainingMode из строки или старого enum."""
    if value is None or isinstance(value, TrainingMode):
        return value
    try:
        return TrainingMode(value)
    except ValueError:
        return None
