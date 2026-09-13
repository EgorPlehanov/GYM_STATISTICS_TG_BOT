from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.fsm.training import TrainingMode, accept_button_by_mode


def get_ikb_accept_addition(
    mode: TrainingMode = TrainingMode.ADD_EXERCISE,
) -> InlineKeyboardMarkup:
    """Создает inline-клавиатуру подтверждения добавления упражнения или подхода.

    Args:
        mode: режим добавления или редактирования.

    Returns:
        Inline-клавиатура экрана подтверждения.
    """
    accept_button = accept_button_by_mode[mode]

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"✅ {accept_button.text} ✅",
            callback_data=accept_button.callback_data,
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить повторения 🔂",
            callback_data="to_repetitions",
        )
    )
    builder.row(InlineKeyboardButton(text="✏️ Изменить вес ⚖️", callback_data="to_weight"))
    if mode == TrainingMode.ADD_EXERCISE:
        builder.row(
            InlineKeyboardButton(
                text="✏️ Изменить упражнение 🏋",
                callback_data="to_exercise",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить кол-во подходов 🔁",
            callback_data="to_sets_count",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить и вернуться в меню ❌",
            callback_data="to_menu",
        )
    )
    return builder.as_markup()

