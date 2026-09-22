"""Тесты UI-контракта календаря тренировки."""

from datetime import date

import pytest
from aiogram.types import InlineKeyboardButton

from app.bot.fsm.training import TrainingCalendarView
from app.bot.ui.training.calendar import (
    TrainingCalendarAction,
    TrainingCalendarCallback,
    TrainingDateSelectionLimits,
    render_training_calendar,
    resolve_training_calendar_interaction,
)


def _back_button() -> InlineKeyboardButton:
    """Создает кнопку выхода, не относящуюся к календарю."""
    return InlineKeyboardButton(text="Отмена", callback_data="cancel")


def _labels(markup) -> list[list[str]]:
    """Возвращает подписи кнопок, сгруппированные по строкам клавиатуры."""
    return [[button.text for button in row] for row in markup.inline_keyboard]


def test_days_view_aligns_available_dates_by_weekday_and_marks_training() -> None:
    """Неделя с доступными днями сохраняет семь колонок с заглушками."""
    markup = render_training_calendar(
        view=TrainingCalendarView.DAYS,
        year=2026,
        month=9,
        training_dates=[date(2026, 9, 3), date(2026, 9, 20)],
        editing_date=date(2026, 9, 20),
        back_button=_back_button(),
        limits=TrainingDateSelectionLimits(date_from=date(2026, 9, 3)),
        today=date(2026, 9, 20),
    )
    rows = _labels(markup)

    assert rows[0] == ["2026", "Сен"]
    assert rows[1] == ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    assert rows[2] == [" ", " ", " ", "✓3", "4", "5", "6"]
    assert all(len(row) == 7 for row in rows[1:-1])
    assert "✎20" in [label for row in rows for label in row]
    assert "✓20" not in [label for row in rows for label in row]
    assert "21" not in [label for row in rows for label in row]


def test_months_view_shows_only_available_months_without_placeholders() -> None:
    """Месяцы строятся по шесть в строке только в доступном диапазоне."""
    markup = render_training_calendar(
        view=TrainingCalendarView.MONTHS,
        year=2026,
        month=None,
        training_dates=[],
        back_button=_back_button(),
        limits=TrainingDateSelectionLimits(
            date_from=date(2026, 6, 15), date_to=date(2026, 9, 20)
        ),
        today=date(2026, 9, 20),
    )

    assert _labels(markup) == [["2026"], ["Июн", "Июл", "Авг", "Сен"], ["Отмена"]]


def test_years_view_shows_navigation_only_when_page_exists() -> None:
    """Стрелки лет появляются лишь для реально доступных соседних страниц."""
    limits = TrainingDateSelectionLimits(
        date_from=date(2002, 1, 1), date_to=date(2012, 12, 31), years_per_row=5
    )
    first_page = render_training_calendar(
        view=TrainingCalendarView.YEARS,
        year=2002,
        month=None,
        training_dates=[],
        back_button=_back_button(),
        limits=limits,
        today=date(2026, 9, 20),
    )
    middle_page = render_training_calendar(
        view=TrainingCalendarView.YEARS,
        year=2007,
        month=None,
        training_dates=[],
        back_button=_back_button(),
        limits=limits,
        today=date(2026, 9, 20),
    )
    last_page = render_training_calendar(
        view=TrainingCalendarView.YEARS,
        year=2012,
        month=None,
        training_dates=[],
        back_button=_back_button(),
        limits=limits,
        today=date(2026, 9, 20),
    )

    assert _labels(first_page) == [
        ["2002", "2003", "2004", "2005", "2006"], ["→"], ["Отмена"]
    ]
    assert _labels(middle_page) == [
        ["2007", "2008", "2009", "2010", "2011"], ["←", "→"], ["Отмена"]
    ]
    assert _labels(last_page) == [
        ["2008", "2009", "2010", "2011", "2012"], ["←"], ["Отмена"]
    ]


def test_resolve_calendar_follows_year_month_day_flow() -> None:
    """Выбор года, месяца и дня возвращает последовательно нужные представления."""
    limits = TrainingDateSelectionLimits(date_from=date(2000, 1, 1), date_to=date(2026, 9, 20))
    years = resolve_training_calendar_interaction(
        TrainingCalendarCallback(
            action=TrainingCalendarAction.OPEN_YEARS, year=2026, month=9, day=0
        ),
        limits=limits,
        today=date(2026, 9, 20),
    )
    months = resolve_training_calendar_interaction(
        TrainingCalendarCallback(
            action=TrainingCalendarAction.SELECT_YEAR, year=2025, month=0, day=0
        ),
        limits=limits,
        today=date(2026, 9, 20),
    )
    days = resolve_training_calendar_interaction(
        TrainingCalendarCallback(
            action=TrainingCalendarAction.SELECT_MONTH, year=2025, month=8, day=0
        ),
        limits=limits,
        today=date(2026, 9, 20),
    )
    selected = resolve_training_calendar_interaction(
        TrainingCalendarCallback(
            action=TrainingCalendarAction.SELECT_DAY, year=2025, month=8, day=18
        ),
        limits=limits,
        today=date(2026, 9, 20),
    )

    assert (years.view, years.year, years.month) == (TrainingCalendarView.YEARS, 2022, None)
    assert (months.view, months.year, months.month) == (TrainingCalendarView.MONTHS, 2025, None)
    assert (days.view, days.year, days.month) == (TrainingCalendarView.DAYS, 2025, 8)
    assert selected.selected_date == date(2025, 8, 18)


def test_years_navigation_uses_window_width_and_normalizes_at_lower_bound() -> None:
    """Переход стрелками равен ширине окна и добирает годы у нижней границы."""
    limits = TrainingDateSelectionLimits(
        date_from=date(2000, 1, 1), date_to=date(2026, 9, 20), years_per_row=5
    )
    previous = resolve_training_calendar_interaction(
        TrainingCalendarCallback(
            action=TrainingCalendarAction.PREVIOUS_YEARS, year=2003, month=0, day=0
        ),
        limits=limits,
        today=date(2026, 9, 20),
    )
    following = resolve_training_calendar_interaction(
        TrainingCalendarCallback(
            action=TrainingCalendarAction.NEXT_YEARS, year=2003, month=0, day=0
        ),
        limits=limits,
        today=date(2026, 9, 20),
    )

    assert previous.year == 2000
    assert following.year == 2008


def test_future_dates_require_explicit_permission() -> None:
    """Будущие даты по умолчанию недоступны и разрешаются отдельным параметром."""
    callback = TrainingCalendarCallback(
        action=TrainingCalendarAction.SELECT_DAY, year=2026, month=9, day=21
    )
    with pytest.raises(ValueError, match="вне доступного диапазона"):
        resolve_training_calendar_interaction(callback, today=date(2026, 9, 20))

    result = resolve_training_calendar_interaction(
        callback,
        limits=TrainingDateSelectionLimits(allow_future_dates=True),
        today=date(2026, 9, 20),
    )

    assert result.selected_date == date(2026, 9, 21)
