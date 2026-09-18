"""Локальная синхронизация одновременных Telegram updates одного пользователя."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class UserChatLockMiddleware(BaseMiddleware):
    """Последовательно обрабатывает updates одного пользователя в одном чате.

    Middleware регистрируется только для сценариев, которые изменяют общий FSM
    draft или редактируют одно и то же Telegram-сообщение. Локальная блокировка
    достаточна для единственного bot-процесса. При горизонтальном
    масштабировании она будет заменена распределенной Redis lock.
    """

    def __init__(self) -> None:
        """Создает пустой набор блокировок пользовательских сценариев."""
        self._locks: dict[tuple[int, int], asyncio.Lock] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Вызывает handler под блокировкой пары chat и user."""
        key = _get_user_chat_key(event)
        if key is None:
            return await handler(event, data)
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            return await handler(event, data)


def _get_user_chat_key(event: TelegramObject) -> tuple[int, int] | None:
    """Извлекает пару chat_id/user_id из сообщения или callback query."""
    if isinstance(event, Message) and event.from_user is not None:
        return event.chat.id, event.from_user.id
    if isinstance(event, CallbackQuery) and event.message is not None:
        return event.message.chat.id, event.from_user.id
    return None
