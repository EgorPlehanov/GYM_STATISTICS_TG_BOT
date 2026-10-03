"""Тесты адаптера операций над контролируемыми Telegram-сообщениями."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramNotFound
from aiogram.methods import DeleteMessage, EditMessageText
from aiogram.types import InputRichMessage

from app.bot.telegram.message_operations import (
    ControlledMessageOperationResult,
    delete_controlled_message,
    edit_controlled_message_reply_markup,
    edit_controlled_message_text,
    edit_controlled_rich_message,
)


async def test_edit_controlled_message_text_returns_applied() -> None:
    """Проверяет успешное изменение текста контролируемого сообщения."""
    bot = SimpleNamespace(edit_message_text=AsyncMock())

    result = await edit_controlled_message_text(
        bot=bot,
        chat_id=1,
        message_id=2,
        text="Обновленный текст",
    )

    assert result is ControlledMessageOperationResult.APPLIED


async def test_edit_controlled_rich_message_passes_rich_content() -> None:
    """Rich-содержимое передается через обычный метод editMessageText."""
    bot = SimpleNamespace(edit_message_text=AsyncMock())
    rich_message = InputRichMessage(html="<h6>Результат</h6>")

    result = await edit_controlled_rich_message(
        bot=bot,
        chat_id=1,
        message_id=2,
        rich_message=rich_message,
    )

    assert result is ControlledMessageOperationResult.APPLIED
    bot.edit_message_text.assert_awaited_once_with(
        chat_id=1,
        message_id=2,
        text=None,
        rich_message=rich_message,
        reply_markup=None,
    )


async def test_edit_controlled_message_reply_markup_returns_not_modified() -> None:
    """Проверяет безопасную обработку неизмененной клавиатуры."""
    bot = SimpleNamespace(
        edit_message_reply_markup=AsyncMock(
            side_effect=TelegramBadRequest(
                method=EditMessageText(chat_id=1, message_id=2, text="text"),
                message="Bad Request: message is not modified",
            )
        )
    )

    result = await edit_controlled_message_reply_markup(
        bot=bot,
        chat_id=1,
        message_id=2,
        reply_markup=None,
    )

    assert result is ControlledMessageOperationResult.NOT_MODIFIED


@pytest.mark.parametrize(
    "error",
    [
        TelegramBadRequest(
            method=EditMessageText(chat_id=1, message_id=2, text="text"),
            message="Bad Request: message to edit not found",
        ),
        TelegramNotFound(
            method=DeleteMessage(chat_id=1, message_id=2),
            message="Not Found",
        ),
    ],
)
async def test_delete_controlled_message_returns_unavailable_for_missing_message(
    error: TelegramBadRequest | TelegramNotFound,
) -> None:
    """Проверяет отсутствие сообщения для 400 и 404 ответов Telegram."""
    bot = SimpleNamespace(delete_message=AsyncMock(side_effect=error))

    result = await delete_controlled_message(bot=bot, chat_id=1, message_id=2)

    assert result is ControlledMessageOperationResult.MESSAGE_UNAVAILABLE


async def test_delete_controlled_message_returns_not_deletable_for_telegram_limit() -> None:
    """Постоянный запрет Telegram на удаление не считается ошибкой сохранения."""
    bot = SimpleNamespace(
        delete_message=AsyncMock(
            side_effect=TelegramBadRequest(
                method=DeleteMessage(chat_id=1, message_id=2),
                message="Bad Request: message can't be deleted",
            )
        )
    )

    result = await delete_controlled_message(bot=bot, chat_id=1, message_id=2)

    assert result is ControlledMessageOperationResult.NOT_DELETABLE


async def test_edit_controlled_message_reraises_unknown_bad_request() -> None:
    """Проверяет, что неизвестный BadRequest не выдает сообщение за удаленное."""
    error = TelegramBadRequest(
        method=EditMessageText(chat_id=1, message_id=2, text="text"),
        message="Bad Request: can't parse entities",
    )
    bot = SimpleNamespace(edit_message_text=AsyncMock(side_effect=error))

    with pytest.raises(TelegramBadRequest, match="can't parse entities"):
        await edit_controlled_message_text(
            bot=bot,
            chat_id=1,
            message_id=2,
            text="<broken>",
        )
