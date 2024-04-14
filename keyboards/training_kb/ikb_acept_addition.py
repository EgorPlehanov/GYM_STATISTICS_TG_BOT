from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.training_units import TrainingMode, acept_button_by_mode


def get_ikb_acept_addition(
    mode: TrainingMode = TrainingMode.ADD_EXERCISE,
) -> InlineKeyboardMarkup:
    """
    Фабрика инлайн клавиатуры подтверждения добавления упражнения/подхода
    """
    acept_button = acept_button_by_mode[mode]

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f"✅ {acept_button.text} ✅", callback_data=acept_button.callback_data))
    builder.row(InlineKeyboardButton(text="✏️ Изменить повторения 🔂", callback_data="to_repetitions"))
    builder.row(InlineKeyboardButton(text="✏️ Изменить вес ⚖️", callback_data="to_weight"))
    if mode == TrainingMode.ADD_EXERCISE:
        builder.row(InlineKeyboardButton(text="✏️ Изменить упражнение 🏋", callback_data="to_exercise"))
    builder.row(InlineKeyboardButton(text="✏️ Изменить кол-во подходов 🔁", callback_data="to_sets_count"))
    return builder.as_markup()