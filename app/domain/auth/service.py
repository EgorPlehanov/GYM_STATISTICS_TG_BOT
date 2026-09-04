"""Сервис авторизации."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.security import is_auth_date_fresh, is_telegram_login_hash_valid
from app.db.models import User
from app.domain.users.service import create_or_update_user_from_telegram


@dataclass(frozen=True)
class TelegramLoginData:
    """Данные, полученные от Telegram Login Widget."""

    id: int
    first_name: str
    auth_date: int
    hash: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None


class AuthService:
    """Бизнес-сценарии авторизации."""


def build_display_name(login_data: TelegramLoginData) -> str:
    """Собирает отображаемое имя пользователя из Telegram-данных."""
    parts = [login_data.first_name, login_data.last_name]
    name = " ".join(part for part in parts if part)
    return name or login_data.username or str(login_data.id)


async def authenticate_telegram_login(
    session: AsyncSession,
    login_data: TelegramLoginData,
) -> User:
    """Авторизует пользователя через Telegram Login Widget.

    Вход:
        session: асинхронная SQLAlchemy-сессия.
        login_data: подписанные Telegram-данные пользователя.

    Выход:
        существующий или созданный пользователь приложения.

    Исключения:
        `ValueError`, если подпись Telegram неверная или payload устарел.
    """
    auth_data = {
        "id": login_data.id,
        "first_name": login_data.first_name,
        "last_name": login_data.last_name,
        "username": login_data.username,
        "photo_url": login_data.photo_url,
        "auth_date": login_data.auth_date,
        "hash": login_data.hash,
    }
    bot_token = config.TG_BOT_TOKEN.get_secret_value()

    if not is_telegram_login_hash_valid(auth_data, bot_token):
        raise ValueError("Неверная подпись Telegram Login Widget")

    if not is_auth_date_fresh(login_data.auth_date):
        raise ValueError("Данные Telegram Login Widget устарели")

    return await create_or_update_user_from_telegram(
        session=session,
        telegram_id=login_data.id,
        name=build_display_name(login_data),
        language_code=None,
    )
