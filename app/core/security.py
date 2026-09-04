"""Вспомогательные функции безопасности."""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import config

SESSION_TOKEN_ALGORITHM = "HS256"


def create_session_token(
    user_id: int,
    telegram_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Создает подписанный токен web-сессии.

    Вход:
        user_id: внутренний id пользователя.
        telegram_id: внешний Telegram user id.
        expires_delta: срок жизни токена. Если не передан, используется настройка проекта.

    Выход:
        JWT-строка для хранения в `httpOnly` cookie.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(seconds=config.SESSION_TTL_SECONDS)
    )
    payload = {
        "sub": str(user_id),
        "telegram_id": telegram_id,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(
        payload,
        config.SESSION_SECRET_KEY.get_secret_value(),
        algorithm=SESSION_TOKEN_ALGORITHM,
    )


def decode_session_token(token: str) -> dict[str, Any]:
    """Проверяет подпись session token и возвращает его payload.

    Вход:
        token: JWT из cookie пользователя.

    Выход:
        словарь claims, если токен подписан корректно и не истек.

    Исключения:
        `jwt.PyJWTError`, если токен недействителен.
    """
    return jwt.decode(
        token,
        config.SESSION_SECRET_KEY.get_secret_value(),
        algorithms=[SESSION_TOKEN_ALGORITHM],
    )


def build_telegram_login_data_check_string(auth_data: dict[str, Any]) -> str:
    """Собирает строку проверки Telegram Login Widget.

    Вход:
        auth_data: данные, полученные от Telegram Login Widget.

    Выход:
        строки `key=value`, отсортированные по ключу и разделенные `\n`.
        Поле `hash` исключается, как требует Telegram.
    """
    return "\n".join(
        f"{key}={value}"
        for key, value in sorted(auth_data.items())
        if key != "hash" and value is not None
    )


def calculate_telegram_login_hash(auth_data: dict[str, Any], bot_token: str) -> str:
    """Рассчитывает hash для проверки Telegram Login Widget.

    Алгоритм соответствует документации Telegram Login Widget: secret key - SHA256
    от bot token, подпись - HMAC-SHA-256 от data-check-string.
    """
    data_check_string = build_telegram_login_data_check_string(auth_data)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    return hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()


def is_telegram_login_hash_valid(auth_data: dict[str, Any], bot_token: str) -> bool:
    """Проверяет, что данные Telegram Login Widget подписаны Telegram."""
    expected_hash = calculate_telegram_login_hash(auth_data, bot_token)
    received_hash = str(auth_data.get("hash", ""))
    return hmac.compare_digest(expected_hash, received_hash)


def is_auth_date_fresh(auth_date: int, max_age_seconds: int = 60 * 60 * 24) -> bool:
    """Проверяет, что Telegram auth payload не устарел.

    Вход:
        auth_date: Unix timestamp из Telegram Login Widget.
        max_age_seconds: максимально допустимый возраст payload.
    """
    now_timestamp = int(datetime.now(timezone.utc).timestamp())
    return 0 <= now_timestamp - auth_date <= max_age_seconds
