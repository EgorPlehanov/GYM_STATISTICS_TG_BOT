"""Сервис авторизации."""

import json
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.security import (
    is_auth_date_fresh,
    is_telegram_login_hash_valid,
    is_telegram_mini_app_hash_valid,
    parse_telegram_mini_app_init_data,
)
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


@dataclass(frozen=True)
class TelegramMiniAppUserData:
    """Данные пользователя из проверенного Telegram Mini App initData."""

    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    photo_url: str | None = None


class AuthService:
    """Бизнес-сценарии авторизации."""


def build_display_name(
    telegram_id: int,
    first_name: str,
    last_name: str | None = None,
    username: str | None = None,
) -> str:
    """Собирает отображаемое имя пользователя из Telegram-данных."""
    parts = [first_name, last_name]
    name = " ".join(part for part in parts if part)
    return name or username or str(telegram_id)


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
        name=build_display_name(
            telegram_id=login_data.id,
            first_name=login_data.first_name,
            last_name=login_data.last_name,
            username=login_data.username,
        ),
        language_code=None,
    )


async def authenticate_telegram_mini_app(
    session: AsyncSession,
    init_data: str,
) -> User:
    """Авторизует пользователя через Telegram Mini App initData.

    Вход:
        session: асинхронная SQLAlchemy-сессия.
        init_data: raw query string из `Telegram.WebApp.initData`.

    Выход:
        существующий или созданный пользователь приложения.

    Исключения:
        `ValueError`, если initData повреждены, подпись неверная, payload устарел
        или в payload нет пользователя.
    """
    try:
        init_data_values = parse_telegram_mini_app_init_data(init_data)
    except ValueError as exc:
        raise ValueError("Некорректный формат Telegram Mini App initData") from exc

    bot_token = config.TG_BOT_TOKEN.get_secret_value()
    if not is_telegram_mini_app_hash_valid(init_data_values, bot_token):
        raise ValueError("Неверная подпись Telegram Mini App initData")

    try:
        auth_date = int(init_data_values["auth_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("В Telegram Mini App initData нет корректного auth_date") from exc

    if not is_auth_date_fresh(auth_date):
        raise ValueError("Данные Telegram Mini App initData устарели")

    try:
        raw_user_data = json.loads(init_data_values["user"])
        user_data = TelegramMiniAppUserData(
            id=raw_user_data["id"],
            first_name=raw_user_data["first_name"],
            last_name=raw_user_data.get("last_name"),
            username=raw_user_data.get("username"),
            language_code=raw_user_data.get("language_code"),
            photo_url=raw_user_data.get("photo_url"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("В Telegram Mini App initData нет корректного пользователя") from exc

    return await create_or_update_user_from_telegram(
        session=session,
        telegram_id=user_data.id,
        name=build_display_name(
            telegram_id=user_data.id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            username=user_data.username,
        ),
        language_code=user_data.language_code,
    )
