"""Вспомогательные функции безопасности."""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qsl

import jwt

from app.core.config import config

SESSION_TOKEN_ALGORITHM = "HS256"


def create_session_token(
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Создает подписанный токен web-сессии.

    Args:
        user_id: внутренний id пользователя.
        expires_delta: срок жизни токена. Если не передан, используется настройка проекта.

    Returns:
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

    Args:
        token: JWT из cookie пользователя.

    Returns:
        словарь claims, если токен подписан корректно и не истек.

    Raises:
        `jwt.PyJWTError`, если токен недействителен.
    """
    return jwt.decode(
        token,
        config.SESSION_SECRET_KEY.get_secret_value(),
        algorithms=[SESSION_TOKEN_ALGORITHM],
    )


def build_telegram_login_data_check_string(auth_data: dict[str, Any]) -> str:
    """Собирает строку проверки Telegram Login Widget.

    Args:
        auth_data: данные, полученные от Telegram Login Widget.

    Returns:
        строки `key=value`, отсортированные по ключу и разделенные `\\n`.
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


def parse_telegram_mini_app_init_data(init_data: str) -> dict[str, str]:
    """Парсит raw `Telegram.WebApp.initData` в словарь строковых параметров.

    Args:
        init_data: query string из `Telegram.WebApp.initData`.

    Returns:
        словарь параметров после URL-decoding.
    """
    return dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))


def build_telegram_mini_app_data_check_string(init_data_values: dict[str, str]) -> str:
    """Собирает строку проверки Telegram Mini App initData.

    Args:
        init_data_values: распарсенные параметры `Telegram.WebApp.initData`.

    Returns:
        строки `key=value`, отсортированные по ключу и разделенные `\n`.
        Поля `hash` и `signature` исключаются из строки проверки.
    """
    return "\n".join(
        f"{key}={value}"
        for key, value in sorted(init_data_values.items())
        if key not in {"hash", "signature"}
    )


def calculate_telegram_mini_app_hash(init_data_values: dict[str, str], bot_token: str) -> str:
    """Рассчитывает hash для проверки Telegram Mini App initData.

    Алгоритм отличается от Telegram Login Widget: промежуточный secret key
    получается через HMAC-SHA-256 от bot token с ключом `WebAppData`.
    """
    data_check_string = build_telegram_mini_app_data_check_string(init_data_values)
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256,
    ).digest()
    return hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()


def is_telegram_mini_app_hash_valid(init_data_values: dict[str, str], bot_token: str) -> bool:
    """Проверяет, что Mini App initData подписаны Telegram."""
    expected_hash = calculate_telegram_mini_app_hash(init_data_values, bot_token)
    received_hash = init_data_values.get("hash", "")
    return hmac.compare_digest(expected_hash, received_hash)


def is_auth_date_fresh(auth_date: int, max_age_seconds: int = 60 * 60 * 24) -> bool:
    """Проверяет, что Telegram auth payload не устарел.

    Args:
        auth_date: Unix timestamp из Telegram Login Widget.
        max_age_seconds: максимально допустимый возраст payload.
    """
    now_timestamp = int(datetime.now(timezone.utc).timestamp())
    return 0 <= now_timestamp - auth_date <= max_age_seconds
