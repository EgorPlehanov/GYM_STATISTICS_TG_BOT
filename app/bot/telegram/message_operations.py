"""Операции над контролируемыми Telegram-сообщениями."""

from enum import Enum

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNotFound
from aiogram.types import InlineKeyboardMarkup, InputRichMessage


class ControlledMessageOperationResult(str, Enum):
    """Результат операции над известным Telegram-сообщением."""

    APPLIED = "applied"
    NOT_MODIFIED = "not_modified"
    MESSAGE_UNAVAILABLE = "message_unavailable"
    NOT_DELETABLE = "not_deletable"


async def edit_controlled_message_text(
    *,
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> ControlledMessageOperationResult:
    """Изменяет текст известного сообщения и классифицирует ожидаемые ответы Telegram.

    Args:
        bot: экземпляр aiogram Bot.
        chat_id: Telegram chat id сообщения.
        message_id: id сообщения, которое должно существовать в чате.
        text: новый текст сообщения.
        reply_markup: новая inline-клавиатура или `None` для ее удаления.

    Returns:
        результат операции над контролируемым сообщением.

    Raises:
        TelegramBadRequest: если Telegram вернул неизвестную ошибку запроса.
        TelegramForbiddenError: если бот не может работать с чатом.
        TelegramRetryAfter: при превышении лимита Telegram.
        TelegramNetworkError: при сетевой ошибке.
        TelegramServerError: при ошибке Telegram 5xx.
    """
    return await _edit_controlled_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=reply_markup,
    )


async def edit_controlled_rich_message(
    *,
    bot: Bot,
    chat_id: int,
    message_id: int,
    rich_message: InputRichMessage,
) -> ControlledMessageOperationResult:
    """Изменяет Rich Message и классифицирует ожидаемые ответы Telegram.

    Args:
        bot: экземпляр aiogram Bot.
        chat_id: Telegram chat id сообщения.
        message_id: id сообщения, которое должно существовать в чате.
        rich_message: новое структурированное содержимое сообщения.

    Returns:
        результат операции над контролируемым сообщением.
    """
    return await _edit_controlled_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        rich_message=rich_message,
    )


async def edit_controlled_message_reply_markup(
    *,
    bot: Bot,
    chat_id: int,
    message_id: int,
    reply_markup: InlineKeyboardMarkup | None,
) -> ControlledMessageOperationResult:
    """Изменяет клавиатуру известного сообщения и классифицирует ответы Telegram.

    Args:
        bot: экземпляр aiogram Bot.
        chat_id: Telegram chat id сообщения.
        message_id: id сообщения, которое должно существовать в чате.
        reply_markup: новая inline-клавиатура или `None` для ее удаления.

    Returns:
        результат операции над контролируемым сообщением.

    Raises:
        TelegramBadRequest: если Telegram вернул неизвестную ошибку запроса.
        TelegramForbiddenError: если бот не может работать с чатом.
        TelegramRetryAfter: при превышении лимита Telegram.
        TelegramNetworkError: при сетевой ошибке.
        TelegramServerError: при ошибке Telegram 5xx.
    """
    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
        )
    except (TelegramBadRequest, TelegramNotFound) as error:
        return _classify_controlled_message_error(error)
    return ControlledMessageOperationResult.APPLIED


async def delete_controlled_message(
    *,
    bot: Bot,
    chat_id: int,
    message_id: int,
) -> ControlledMessageOperationResult:
    """Удаляет известное сообщение и классифицирует ответы Telegram.

    Args:
        bot: экземпляр aiogram Bot.
        chat_id: Telegram chat id сообщения.
        message_id: id сообщения, которое должно существовать в чате.

    Returns:
        результат операции над контролируемым сообщением.

    Raises:
        TelegramBadRequest: если Telegram вернул неизвестную ошибку запроса.
        TelegramForbiddenError: если бот не может работать с чатом.
        TelegramRetryAfter: при превышении лимита Telegram.
        TelegramNetworkError: при сетевой ошибке.
        TelegramServerError: при ошибке Telegram 5xx.
    """
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except (TelegramBadRequest, TelegramNotFound) as error:
        return _classify_delete_message_error(error)
    return ControlledMessageOperationResult.APPLIED


def _classify_controlled_message_error(
    error: TelegramBadRequest | TelegramNotFound,
) -> ControlledMessageOperationResult:
    """Преобразует только подтвержденные ошибки сообщения в typed-результат."""
    if isinstance(error, TelegramNotFound):
        return ControlledMessageOperationResult.MESSAGE_UNAVAILABLE

    message = error.message.lower()
    if "message is not modified" in message:
        return ControlledMessageOperationResult.NOT_MODIFIED
    if (
        "message to edit not found" in message
        or "message to delete not found" in message
    ):
        return ControlledMessageOperationResult.MESSAGE_UNAVAILABLE
    raise error


def _classify_delete_message_error(
    error: TelegramBadRequest | TelegramNotFound,
) -> ControlledMessageOperationResult:
    """Дополняет общую классификацию постоянным запретом Telegram на удаление."""
    if (
        isinstance(error, TelegramBadRequest)
        and "message can't be deleted" in error.message.lower()
    ):
        return ControlledMessageOperationResult.NOT_DELETABLE
    return _classify_controlled_message_error(error)


async def _edit_controlled_message(
    *,
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str | None = None,
    rich_message: InputRichMessage | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> ControlledMessageOperationResult:
    """Вызывает общий editMessageText для обычного или Rich-содержимого."""
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            rich_message=rich_message,
            reply_markup=reply_markup,
        )
    except (TelegramBadRequest, TelegramNotFound) as error:
        return _classify_controlled_message_error(error)
    return ControlledMessageOperationResult.APPLIED
