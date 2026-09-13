"""Глобальная обработка ошибок Telegram-бота."""

import traceback
from io import BytesIO
from typing import Any

from aiogram import Bot, Router, html
from aiogram.types import BufferedInputFile, ErrorEvent

from app.bot.formatters.messages import split_message_with_tags
from app.core.config import config

router = Router()


@router.error()
async def error_handler(event: ErrorEvent) -> None:
    """Обрабатывает ошибки Telegram-бота и отправляет traceback главному администратору."""
    obj = _get_event_object(event)
    bot: Bot | None = getattr(obj, "bot", None)
    chat = getattr(obj, "chat", None)

    if bot is None:
        return

    if chat is not None and chat.id != config.MAIN_ADMIN_ID.get_secret_value():
        event_type = html.underline(event.update.event_type)
        error_type = html.pre_language(html.quote(str(type(event.exception))), "python")
        user_message = (
            f"❗{html.bold(f' При обработке события {event_type} произошла ошибка:')}\n"
            f"{error_type}\n"
            f"❗{html.bold(' Пожалуйста сделайте скриншот и опишите администратору ')}"
            f"{html.bold('контекст, в котором произошла ошибка')}"
        )
        await bot.send_message(
            chat_id=chat.id,
            text=user_message,
        )

    exception_text = _format_exception_text(event)
    traceback_buffer = _get_traceback_buffer()
    text_parts = split_message_with_tags(exception_text, True)

    await bot.send_document(
        chat_id=config.MAIN_ADMIN_ID.get_secret_value(),
        document=BufferedInputFile(
            file=traceback_buffer,
            filename="traceback.txt",
        ),
        caption=text_parts[0],
    )
    for text_part in text_parts[1:]:
        await bot.send_message(
            chat_id=config.MAIN_ADMIN_ID.get_secret_value(),
            text=text_part,
        )


def _get_event_object(event: ErrorEvent) -> Any:
    """Возвращает Telegram-объект, при обработке которого возникла ошибка."""
    return getattr(event.update, event.update.event_type, None)


def _format_exception_text(event: ErrorEvent) -> str:
    """Формирует техническое сообщение об ошибке для главного администратора."""
    exception_text = (
        f"{html.bold('Произошла ошибка при обработке события:')}\n"
        f"{html.blockquote(html.quote(event.update.event_type))}\n"
        f"{html.bold('Тип ошибки:')}\n"
        f"{html.pre_language(html.quote(str(type(event.exception))), 'python')}\n"
        f"{html.bold('Ошибка:')}\n"
        f"{html.pre_language(html.quote(str(event.exception)), 'python')}\n"
    )
    if event.exception.args:
        exception_text += (
            f"{html.bold('Аргументы:')}\n"
            f"{html.pre_language(html.quote(str(event.exception.args)), 'python')}\n"
        )

    return (
        "❗❗❗❗❗\n"
        f"{exception_text}"
        "❗❗❗❗❗"
    )


def _get_traceback_buffer() -> bytes:
    """Возвращает текущий traceback в виде байтов для отправки файлом."""
    buffer = BytesIO()
    buffer.write(traceback.format_exc().encode())
    buffer.seek(0)
    return buffer.getvalue()
