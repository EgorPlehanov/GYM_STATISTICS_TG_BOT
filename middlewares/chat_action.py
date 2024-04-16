from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.dispatcher.flags import get_flag
from aiogram.utils.chat_action import ChatActionSender

from typing import Callable, Dict, Any, Awaitable



class ChatActionMiddleware(BaseMiddleware):
    """
    Миддлвейр для отправки действий бота в чате
    
    chat_action_type:
        typing: печатает
        upload_photo: загружает фото
        record_video: записывает видео
        upload_video: загружает видео
        record_voice: записывает голосовое сообщение
        upload_voice: загружает голосовое сообщение
        upload_document: загружает документ
        choose_sticker: выбирает стикер
        find_location: поиск локации
        record_video_note: записывает видео-кружок
        upload_video_note: загружает видео-кружок
    """
    def __init__(self, default_chat_action_type: str = None):
        self.default_chat_action_type = default_chat_action_type


    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        chat_action_type = get_flag(data, "chat_action", default=self.default_chat_action_type)

        # Если такого флага на хэндлере нет
        if not chat_action_type:
            return await handler(event, data)

        # Если флаг есть
        async with ChatActionSender(
            bot = event.bot,
            action = chat_action_type, 
            chat_id = event.chat.id
        ):
            return await handler(event, data)