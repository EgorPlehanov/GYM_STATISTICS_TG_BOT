"""Rich Message-представление результата тренировки для redirect-групп."""

from datetime import date, datetime

from aiogram import html
from aiogram.types import InputRichMessage

from app.bot.formatters.training import result_format_exercise_sets_from_draft
from app.bot.fsm.training import TrainingDraft, TrainingDraftSet

WEEKDAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
MONTHS_GENITIVE = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def format_redirect_training_result(
    draft: TrainingDraft,
    *,
    telegram_id: int,
    user_full_name: str,
) -> InputRichMessage:
    """Строит Rich HTML результата сохраненной тренировки для группы.

    Args:
        draft: сохраненный снимок тренировки без временных UI-меток.
        telegram_id: id владельца тренировки для ссылки на Telegram-профиль.
        user_full_name: отображаемое имя владельца тренировки.

    Returns:
        Rich Message с заголовком, непустыми блоками тренировки и сводкой.

    Raises:
        ValueError: если у тренировки нет даты.
    """
    training_date = _training_date(draft.training.training_date)
    content = [_format_header(training_date, telegram_id, user_full_name)]

    comment = draft.training.comment
    if comment is not None and comment.strip():
        content.append(f"<blockquote>{html.quote(comment.strip())}</blockquote>")

    rows = [
        _format_exercise_row(exercise.exercise_name, exercise.sets)
        for exercise in draft.training.exercises
        if exercise.sets
    ]
    if rows:
        content.append("<table bordered striped compact>" + "".join(rows) + "</table>")
        exercise_count = len(rows)
        sets_count = sum(len(exercise.sets) for exercise in draft.training.exercises)
        exercise_label = _pluralize(
            exercise_count,
            "упражнение",
            "упражнения",
            "упражнений",
        )
        sets_label = _pluralize(sets_count, "подход", "подхода", "подходов")
        content.append(
            "<footer>"
            f"{exercise_count} {exercise_label}"
            " · "
            f"{sets_count} {sets_label}"
            "</footer>"
        )

    # Статистика прогресса появится здесь только при наличии рассчитанных данных.
    return InputRichMessage(html="".join(content))


def _training_date(value: str | date | datetime | None) -> date:
    """Преобразует JSON-friendly дату draft в календарную дату."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError("Для redirect-сообщения требуется дата тренировки")


def _format_header(training_date: date, telegram_id: int, user_full_name: str) -> str:
    """Формирует заголовок с безопасной ссылкой на профиль владельца."""
    date_text = (
        f"{WEEKDAYS[training_date.weekday()]}, "
        f"{training_date.day} {MONTHS_GENITIVE[training_date.month - 1]}"
    )
    return (
        "<h6>"
        f'<a href="tg://user?id={telegram_id}">{html.quote(user_full_name)}</a>'
        f" · {date_text}"
        "</h6>"
    )


def _format_exercise_row(exercise_name: str, sets: list[TrainingDraftSet]) -> str:
    """Формирует непустую строку таблицы одного упражнения."""
    return (
        "<tr>"
        f"<td>{html.quote(exercise_name)}</td>"
        f"<td>{result_format_exercise_sets_from_draft(sets)}</td>"
        "</tr>"
    )


def _pluralize(number: int, singular: str, paucal: str, plural: str) -> str:
    """Выбирает русскую форму существительного для количества."""
    remainder = number % 100
    if 11 <= remainder <= 14:
        return plural
    remainder = number % 10
    if remainder == 1:
        return singular
    if 2 <= remainder <= 4:
        return paucal
    return plural
