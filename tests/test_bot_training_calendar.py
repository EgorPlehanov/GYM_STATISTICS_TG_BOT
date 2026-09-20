"""Тесты самостоятельного UI-контракта календаря тренировки."""

from datetime import date

import pytest
from aiogram.types import InlineKeyboardButton

from app.bot.ui.training.calendar import (
    TrainingCalendarAction,
    TrainingCalendarCallback,
    render_training_calendar,
    resolve_training_calendar_interaction,
)


def test_render_training_calendar_marks_today_and_training_date() -> None:
    """Проверяет отметки сегодняшнего дня и сохраненной тренировки."""
    markup = render_training_calendar(
        year=2026,
        month=9,
        training_dates=[date(2026, 9, 11), date(2026, 9, 20)],
        back_button=InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        today=date(2026, 9, 20),
    )

    labels = [button.text for row in markup.inline_keyboard for button in row]

    assert "✓11" in labels
    assert "✓20" in labels
    assert "📍20" not in labels
    assert "21" not in labels


def test_render_training_calendar_allows_next_month_only_before_current_month() -> None:
    """Проверяет доступность перехода вперед только до текущего месяца."""
    historical_markup = render_training_calendar(
        year=2026,
        month=8,
        training_dates=[],
        back_button=InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        today=date(2026, 9, 20),
    )
    current_markup = render_training_calendar(
        year=2026,
        month=9,
        training_dates=[],
        back_button=InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        today=date(2026, 9, 20),
    )

    assert historical_markup.inline_keyboard[0][2].text == "›"
    assert current_markup.inline_keyboard[0][2].text == " "


def test_resolve_training_calendar_interaction_moves_to_previous_month() -> None:
    """Проверяет переход на предыдущий месяц по typed callback-данным."""
    result = resolve_training_calendar_interaction(
        TrainingCalendarCallback(
            action=TrainingCalendarAction.PREVIOUS_MONTH,
            year=2026,
            month=1,
            day=0,
        ),
        today=date(2026, 9, 20),
    )

    assert (result.year, result.month, result.selected_date) == (2025, 12, None)


def test_resolve_training_calendar_interaction_returns_selected_date() -> None:
    """Проверяет возврат выбранной даты без Telegram API-вызова."""
    result = resolve_training_calendar_interaction(
        TrainingCalendarCallback(
            action=TrainingCalendarAction.SELECT_DAY,
            year=2026,
            month=9,
            day=18,
        ),
        today=date(2026, 9, 20),
    )

    assert result.selected_date == date(2026, 9, 18)


def test_resolve_training_calendar_interaction_rejects_future_day() -> None:
    """Проверяет защиту от callback с будущей датой."""
    with pytest.raises(ValueError, match="будущую дату"):
        resolve_training_calendar_interaction(
            TrainingCalendarCallback(
                action=TrainingCalendarAction.SELECT_DAY,
                year=2026,
                month=9,
                day=21,
            ),
            today=date(2026, 9, 20),
        )
