"""Построение и обработка действий календаря тренировки."""

import calendar
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.fsm.training import TrainingCalendarView

_MONTH_NAMES_SHORT = (
    "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
    "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек",
)
_WEEKDAY_NAMES = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


@dataclass(frozen=True, slots=True)
class TrainingDateSelectionLimits:
    """Ограничения доступных дат в календаре тренировки.

    Attributes:
        date_from: самая ранняя доступная дата.
        date_to: явная верхняя граница или `None`, если она не задана.
        allow_future_dates: разрешает ли выбирать дни позднее текущей даты.
        years_per_row: число лет в одной странице и строке выбора лет.
    """

    date_from: date = date(2000, 1, 1)
    date_to: date | None = None
    allow_future_dates: bool = False
    years_per_row: int = 5


DEFAULT_TRAINING_DATE_SELECTION_LIMITS = TrainingDateSelectionLimits()


class TrainingCalendarAction(str, Enum):
    """Действия, доступные в inline-календаре тренировки."""

    IGNORE = "ignore"
    OPEN_YEARS = "open_years"
    OPEN_MONTHS = "open_months"
    PREVIOUS_YEARS = "previous_years"
    NEXT_YEARS = "next_years"
    SELECT_YEAR = "select_year"
    SELECT_MONTH = "select_month"
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
        view: представление, которое следует показать после действия.
        year: год выбранного месяца либо начало страницы лет.
        month: номер месяца на экране дней или `None` на других экранах.
        selected_date: выбранная дата или `None`, если пользователь навигировал.
    """

    view: TrainingCalendarView
    year: int
    month: int | None = None
    selected_date: date | None = None


def render_training_calendar(
    *,
    view: TrainingCalendarView = TrainingCalendarView.DAYS,
    year: int,
    month: int | None,
    training_dates: Iterable[date],
    back_button: InlineKeyboardButton,
    limits: TrainingDateSelectionLimits = DEFAULT_TRAINING_DATE_SELECTION_LIMITS,
    today: date | None = None,
) -> InlineKeyboardMarkup:
    """Строит одно из представлений inline-календаря тренировки.

    Args:
        view: экран дней, месяцев или лет.
        year: год месяца либо начало страницы лет.
        month: номер месяца для экрана дней; для остальных экранов не нужен.
        training_dates: даты уже сохраненных тренировок пользователя.
        back_button: кнопка выхода в контекст, из которого открыт календарь.
        limits: ограничения диапазона и навигации по календарю.
        today: текущая дата; параметр нужен для предсказуемого тестирования.

    Returns:
        Клавиатура календаря для запрошенного представления.
    """
    current_date = today or date.today()
    date_from, date_to = _available_range(limits=limits, today=current_date)
    saved_dates = set(training_dates)

    if view is TrainingCalendarView.DAYS:
        if month is None:
            raise ValueError("Для отображения дней необходимо указать месяц")
        return _render_days(
            year=year, month=month, saved_dates=saved_dates, back_button=back_button,
            date_from=date_from, date_to=date_to, today=current_date,
        )
    if view is TrainingCalendarView.MONTHS:
        return _render_months(
            year=year, back_button=back_button, date_from=date_from, date_to=date_to,
        )
    if view is TrainingCalendarView.YEARS:
        return _render_years(
            page_start=year, back_button=back_button, date_from=date_from, date_to=date_to,
            years_per_row=limits.years_per_row,
        )
    raise ValueError(f"Неподдерживаемое представление календаря: {view}")


def resolve_training_calendar_interaction(
    callback_data: TrainingCalendarCallback,
    *,
    limits: TrainingDateSelectionLimits = DEFAULT_TRAINING_DATE_SELECTION_LIMITS,
    today: date | None = None,
) -> TrainingCalendarInteraction:
    """Преобразует callback календаря в следующий экран или выбранную дату.

    Args:
        callback_data: распакованные callback-данные календаря.
        limits: ограничения диапазона и навигации по календарю.
        today: текущая дата; параметр нужен для предсказуемого тестирования.

    Returns:
        Описание следующего представления и выбранной даты, если она есть.

    Raises:
        ValueError: если callback содержит недоступную дату или навигацию.
    """
    current_date = today or date.today()
    date_from, date_to = _available_range(limits=limits, today=current_date)

    if callback_data.action is TrainingCalendarAction.OPEN_YEARS:
        _validate_year_available(callback_data.year, date_from=date_from, date_to=date_to)
        return TrainingCalendarInteraction(
            view=TrainingCalendarView.YEARS,
            year=_year_page_start(
                year=callback_data.year, first_year=date_from.year,
                years_per_row=limits.years_per_row,
            ),
        )
    if callback_data.action in {
        TrainingCalendarAction.OPEN_MONTHS,
        TrainingCalendarAction.SELECT_YEAR,
    }:
        _validate_year_available(callback_data.year, date_from=date_from, date_to=date_to)
        return TrainingCalendarInteraction(
            view=TrainingCalendarView.MONTHS,
            year=callback_data.year,
        )
    if callback_data.action is TrainingCalendarAction.SELECT_MONTH:
        _validate_month_available(
            year=callback_data.year, month=callback_data.month,
            date_from=date_from, date_to=date_to,
        )
        return TrainingCalendarInteraction(
            view=TrainingCalendarView.DAYS,
            year=callback_data.year,
            month=callback_data.month,
        )
    if callback_data.action in {
        TrainingCalendarAction.PREVIOUS_YEARS,
        TrainingCalendarAction.NEXT_YEARS,
    }:
        current_page = _year_page_start(
            year=callback_data.year, first_year=date_from.year,
            years_per_row=limits.years_per_row,
        )
        offset = -limits.years_per_row
        if callback_data.action is TrainingCalendarAction.NEXT_YEARS:
            offset = limits.years_per_row
        target_page = current_page + offset
        if not date_from.year <= target_page <= date_to.year:
            raise ValueError("Нельзя открыть запрошенную страницу лет")
        return TrainingCalendarInteraction(view=TrainingCalendarView.YEARS, year=target_page)
    if callback_data.action is TrainingCalendarAction.SELECT_DAY:
        selected_date = date(callback_data.year, callback_data.month, callback_data.day)
        if not date_from <= selected_date <= date_to:
            raise ValueError("Выбранная дата находится вне доступного диапазона")
        return TrainingCalendarInteraction(
            view=TrainingCalendarView.DAYS,
            year=callback_data.year,
            month=callback_data.month,
            selected_date=selected_date,
        )
    raise ValueError(f"Неподдерживаемое действие календаря: {callback_data.action}")


def _render_days(
    *, year: int, month: int, saved_dates: set[date], back_button: InlineKeyboardButton,
    date_from: date, date_to: date, today: date,
) -> InlineKeyboardMarkup:
    """Строит экран дней с выравниванием по названиям дней недели."""
    _validate_month_available(year=year, month=month, date_from=date_from, date_to=date_to)
    builder = InlineKeyboardBuilder()
    builder.row(
        _callback_button(text=str(year), action=TrainingCalendarAction.OPEN_YEARS, year=year),
        _callback_button(
            text=_MONTH_NAMES_SHORT[month - 1], action=TrainingCalendarAction.OPEN_MONTHS,
            year=year, month=month,
        ),
    )
    builder.row(*[
        _callback_button(
            text=weekday, action=TrainingCalendarAction.IGNORE, year=year, month=month,
        )
        for weekday in _WEEKDAY_NAMES
    ])

    for week in calendar.Calendar(firstweekday=calendar.MONDAY).monthdayscalendar(year, month):
        day_dates = [date(year, month, day) if day else None for day in week]
        if not any(
            day_date is not None and date_from <= day_date <= date_to
            for day_date in day_dates
        ):
            continue
        builder.row(*[
            _day_button(
                year=year, month=month, day=day, saved_dates=saved_dates,
                date_from=date_from, date_to=date_to, today=today,
            )
            for day in week
        ])

    builder.row(back_button)
    return builder.as_markup()


def _render_months(
    *, year: int, back_button: InlineKeyboardButton, date_from: date, date_to: date,
) -> InlineKeyboardMarkup:
    """Строит экран доступных месяцев выбранного года."""
    _validate_year_available(year, date_from=date_from, date_to=date_to)
    builder = InlineKeyboardBuilder()
    builder.row(
        _callback_button(
            text=str(year),
            action=TrainingCalendarAction.OPEN_YEARS,
            year=year,
        )
    )
    month_buttons = [
        _callback_button(
            text=_MONTH_NAMES_SHORT[month - 1], action=TrainingCalendarAction.SELECT_MONTH,
            year=year, month=month,
        )
        for month in range(1, 13)
        if _is_month_available(year=year, month=month, date_from=date_from, date_to=date_to)
    ]
    for row in _split_rows(month_buttons, size=6):
        builder.row(*row)
    builder.row(back_button)
    return builder.as_markup()


def _render_years(
    *, page_start: int, back_button: InlineKeyboardButton, date_from: date,
    date_to: date, years_per_row: int,
) -> InlineKeyboardMarkup:
    """Строит страницу доступных лет и только доступные стрелки навигации."""
    current_page = _year_page_start(
        year=page_start, first_year=date_from.year, years_per_row=years_per_row,
    )
    _validate_year_available(current_page, date_from=date_from, date_to=date_to)
    builder = InlineKeyboardBuilder()
    builder.row(*[
        _callback_button(text=str(year), action=TrainingCalendarAction.SELECT_YEAR, year=year)
        for year in range(current_page, min(current_page + years_per_row, date_to.year + 1))
    ])

    navigation_buttons = []
    if current_page > date_from.year:
        navigation_buttons.append(_callback_button(
            text="←", action=TrainingCalendarAction.PREVIOUS_YEARS, year=current_page,
        ))
    if current_page + years_per_row <= date_to.year:
        navigation_buttons.append(_callback_button(
            text="→", action=TrainingCalendarAction.NEXT_YEARS, year=current_page,
        ))
    if navigation_buttons:
        builder.row(*navigation_buttons)
    builder.row(back_button)
    return builder.as_markup()


def _callback_button(
    *, text: str, action: TrainingCalendarAction, year: int, month: int = 0, day: int = 0,
) -> InlineKeyboardButton:
    """Создает кнопку с callback-данными календаря."""
    return InlineKeyboardButton(
        text=text,
        callback_data=TrainingCalendarCallback(
            action=action, year=year, month=month, day=day,
        ).pack(),
    )


def _day_button(
    *, year: int, month: int, day: int, saved_dates: set[date], date_from: date,
    date_to: date, today: date,
) -> InlineKeyboardButton:
    """Создает кнопку дня или заглушку для сохранения колонок недели."""
    if day == 0:
        return _callback_button(
            text=" ", action=TrainingCalendarAction.IGNORE, year=year, month=month,
        )
    day_date = date(year, month, day)
    if not date_from <= day_date <= date_to:
        return _callback_button(
            text=" ", action=TrainingCalendarAction.IGNORE, year=year, month=month,
        )
    if day_date in saved_dates:
        text = f"✓{day}"
    elif day_date == today:
        text = f"📍{day}"
    else:
        text = str(day)
    return _callback_button(
        text=text, action=TrainingCalendarAction.SELECT_DAY,
        year=year, month=month, day=day,
    )


def _available_range(*, limits: TrainingDateSelectionLimits, today: date) -> tuple[date, date]:
    """Возвращает фактические границы выбора даты для текущего дня."""
    if limits.years_per_row < 1:
        raise ValueError("Количество лет в строке должно быть положительным")
    if limits.date_to is not None and limits.date_to < limits.date_from:
        raise ValueError("Дата окончания не может быть раньше даты начала")
    date_to = limits.date_to or date.max
    if not limits.allow_future_dates:
        date_to = min(date_to, today)
    if limits.date_from > date_to:
        raise ValueError("В заданном диапазоне нет доступных дат")
    return limits.date_from, date_to


def _validate_year_available(year: int, *, date_from: date, date_to: date) -> None:
    """Проверяет, что в указанном году есть хотя бы одна доступная дата."""
    if not date_from.year <= year <= date_to.year:
        raise ValueError("Год находится вне доступного диапазона")


def _validate_month_available(
    *, year: int, month: int, date_from: date, date_to: date,
) -> None:
    """Проверяет, что в указанном месяце есть хотя бы одна доступная дата."""
    if not 1 <= month <= 12:
        raise ValueError("Номер месяца должен быть в диапазоне от 1 до 12")
    if not _is_month_available(year=year, month=month, date_from=date_from, date_to=date_to):
        raise ValueError("Месяц находится вне доступного диапазона")


def _is_month_available(*, year: int, month: int, date_from: date, date_to: date) -> bool:
    """Проверяет пересечение месяца с доступным диапазоном дат."""
    month_start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    return month_start <= date_to and month_end >= date_from


def _year_page_start(*, year: int, first_year: int, years_per_row: int) -> int:
    """Возвращает начало страницы лет, в которую входит указанный год."""
    return first_year + ((year - first_year) // years_per_row) * years_per_row


def _split_rows(
    buttons: list[InlineKeyboardButton], *, size: int,
) -> Iterable[list[InlineKeyboardButton]]:
    """Разбивает список кнопок на строки заданной длины без заглушек."""
    for start in range(0, len(buttons), size):
        yield buttons[start : start + size]
