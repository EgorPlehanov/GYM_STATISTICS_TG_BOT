"""Клавиатура восстановления незавершенной тренировки."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_ikb_resume_prompt() -> InlineKeyboardMarkup:
    """Создает клавиатуру продолжения или удаления draft тренировки."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Продолжить", callback_data="resume_continue"))
    builder.row(
        InlineKeyboardButton(text="Удалить черновик", callback_data="resume_discard")
    )
    return builder.as_markup()
