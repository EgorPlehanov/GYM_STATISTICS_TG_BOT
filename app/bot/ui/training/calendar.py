"""Построение и обработка действий календаря тренировки."""

import calendar
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

_MONTH_NAMES = (
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)
_WEEKDAY_NAMES = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


class TrainingCalendarAction(str, Enum):
    """Действия, доступные в inline-календаре тренировки."""

    IGNORE = "ignore"
    PREVIOUS_MONTH = "previous_month"
    NEXT_MONTH = "next_month"
    SELECT_DAY = "select_day"


class TrainingCalendarCallback(CallbackData, prefix="training_calendar"):
    """Typed callback-данные календаря тренировки."""

    action: TrainingCalendarAction
    year: int
    month: int
    day: int


@dataclass(frozen=True, slots=True)
class TrainingCalendarInteraction:
    """Результат обработки одного действия календаря.

    Attributes:
        year: год месяца, который следует показать после действия.
        month: номер месяца, который следует показать после действия.
        selected_date: выбранная дата или `None`, если пользователь только
            навигировал по календарю.
    """

    year: int
    month: int
    selected_date: date | None = None


def render_training_calendar(
    *,
    year: int,
    month: int,
    training_dates: Iterable[date],
    back_button: InlineKeyboardButton,
    today: date | None = None,
) -> InlineKeyboardMarkup:
    """Строит inline-календарь для выбора даты тренировки.

    Args:
        year: год открытого месяца.
        month: номер открытого месяца от 1 до 12.
        training_dates: даты уже сохраненных тренировок пользователя.
        back_button: кнопка возврата в контекст, из которого открыт календарь.
        today: текущая дата; параметр нужен для предсказуемого тестирования.

    Returns:
        Клавиатура календаря с навигацией по доступным месяцам.

    Raises:
        ValueError: если месяц некорректен или расположен в будущем.
    """
    current_date = today or date.today()
    _validate_visible_month(year=year, month=month, today=current_date)
    saved_dates = set(training_dates)
    can_move_to_next = _can_move_to_next_month(year=year, month=month, today=current_date)

    builder = InlineKeyboardBuilder()
    builder.row(
        _callback_button(
            text="‹",
            action=TrainingCalendarAction.PREVIOUS_MONTH,
            year=year,
            month=month,
        ),
        _callback_button(
            text=f"{_MONTH_NAMES[month - 1]} {year}",
            action=TrainingCalendarAction.IGNORE,
            year=year,
            month=month,
        ),
        _callback_button(
            text="›" if can_move_to_next else " ",
            action=(
                TrainingCalendarAction.NEXT_MONTH
                if can_move_to_next
                else TrainingCalendarAction.IGNORE
            ),
            year=year,
            month=month,
        ),
    )
    builder.row(
        *[
            _callback_button(
                text=weekday,
                action=TrainingCalendarAction.IGNORE,
                year=year,
                month=month,
            )
            for weekday in _WEEKDAY_NAMES
        ]
    )

    for week in calendar.Calendar(firstweekday=calendar.MONDAY).monthdayscalendar(year, month):
        builder.row(
            *[
                _day_button(
                    year=year,
                    month=month,
                    day=day,
                    training_dates=saved_dates,
                    today=current_date,
                )
                for day in week
            ]
        )

    builder.row(back_button)
    return builder.as_markup()


def resolve_training_calendar_interaction(
    callback_data: TrainingCalendarCallback,
    *,
    today: date | None = None,
) -> TrainingCalendarInteraction:
    """Преобразует callback календаря в следующий месяц или выбранную дату.

    Args:
        callback_data: распакованные callback-данные календаря.
        today: текущая дата; параметр нужен для предсказуемого тестирования.

    Returns:
        Описание следующего отображаемого месяца и выбранной даты, если она есть.

    Raises:
        ValueError: если callback содержит некорректную или будущую дату.
    """
    current_date = today or date.today()
    _validate_visible_month(
        year=callback_data.year,
        month=callback_data.month,
        today=current_date,
    )

    if callback_data.action is TrainingCalendarAction.PREVIOUS_MONTH:
        year, month = _shift_month(callback_data.year, callback_data.month, offset=-1)
        return TrainingCalendarInteraction(year=year, month=month)

    if callback_data.action is TrainingCalendarAction.NEXT_MONTH:
        year, month = _shift_month(callback_data.year, callback_data.month, offset=1)
        _validate_visible_month(year=year, month=month, today=current_date)
        return TrainingCalendarInteraction(year=year, month=month)

    if callback_data.action is TrainingCalendarAction.SELECT_DAY:
        selected_date = date(callback_data.year, callback_data.month, callback_data.day)
        if selected_date > current_date:
            raise ValueError("Нельзя выбрать будущую дату тренировки")
        return TrainingCalendarInteraction(
            year=callback_data.year,
            month=callback_data.month,
            selected_date=selected_date,
        )

    return TrainingCalendarInteraction(year=callback_data.year, month=callback_data.month)


def _callback_button(
    *,
    text: str,
    action: TrainingCalendarAction,
    year: int,
    month: int,
    day: int = 0,
) -> InlineKeyboardButton:
    """Создает кнопку с callback-данными календаря."""
    return InlineKeyboardButton(
        text=text,
        callback_data=TrainingCalendarCallback(
            action=action,
            year=year,
            month=month,
            day=day,
        ).pack(),
    )


def _day_button(
    *,
    year: int,
    month: int,
    day: int,
    training_dates: set[date],
    today: date,
) -> InlineKeyboardButton:
    """Создает кнопку одного дня или пустую ячейку месяца."""
    if day == 0:
        return _callback_button(
            text=" ",
            action=TrainingCalendarAction.IGNORE,
            year=year,
            month=month,
        )

    day_date = date(year, month, day)
    if day_date > today:
        return _callback_button(
            text=" ",
            action=TrainingCalendarAction.IGNORE,
            year=year,
            month=month,
        )

    if day_date in training_dates:
        text = f"✓{day}"
    elif day_date == today:
        text = f"📍{day}"
    else:
        text = str(day)

    return _callback_button(
        text=text,
        action=TrainingCalendarAction.SELECT_DAY,
        year=year,
        month=month,
        day=day,
    )


def _can_move_to_next_month(*, year: int, month: int, today: date) -> bool:
    """Проверяет, существует ли следующий доступный для просмотра месяц."""
    next_year, next_month = _shift_month(year, month, offset=1)
    return (next_year, next_month) <= (today.year, today.month)


def _shift_month(year: int, month: int, *, offset: int) -> tuple[int, int]:
    """Сдвигает пару года и месяца на указанное число месяцев."""
    total_months = year * 12 + (month - 1) + offset
    return total_months // 12, total_months % 12 + 1


def _validate_visible_month(*, year: int, month: int, today: date) -> None:
    """Проверяет корректность и доступность месяца для просмотра."""
    if year < 1:
        raise ValueError("Год должен быть положительным числом")
    if not 1 <= month <= 12:
        raise ValueError("Номер месяца должен быть в диапазоне от 1 до 12")
    if (year, month) > (today.year, today.month):
        raise ValueError("Нельзя открыть будущий месяц")
