"""DTO-схемы internal API для пользователей Telegram-бота."""

from pydantic import BaseModel


class InternalBotUserEnsureRequest(BaseModel):
    """Данные пользователя Telegram, которого нужно зарегистрировать для бота."""

    telegram_id: int
    name: str
    language_code: str | None = None


class InternalBotUserEnsureResponse(BaseModel):
    """Результат регистрации пользователя из Telegram-бота."""

    created: bool


class InternalBotUserPrivateChatBannedRequest(BaseModel):
    """Данные для обновления блокировки бота пользователем.

    Attributes:
        is_private_chat_banned: признак того, что пользователь заблокировал бота.
    """

    is_private_chat_banned: bool
