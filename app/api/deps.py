"""Зависимости FastAPI."""

from collections.abc import AsyncGenerator
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.security import decode_session_token
from app.db.models import User
from app.db.session import async_session_factory
from app.domain.users.service import get_user_by_id


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Возвращает асинхронную DB-сессию для одного HTTP-запроса.

    Выход:
        `AsyncSession`, которая автоматически закрывается после обработки запроса.
    """
    async with async_session_factory() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db_session)]
SessionTokenCookie = Annotated[str | None, Cookie(alias=config.SESSION_COOKIE_NAME)]


async def get_current_user(
    session: DbSession,
    session_token: SessionTokenCookie = None,
) -> User:
    """Возвращает пользователя, связанного с текущей web-сессией.

    Вход:
        session_token: подписанный JWT из `httpOnly` cookie.

    Выход:
        объект пользователя из базы данных.

    Исключения:
        `HTTPException 401`, если cookie нет, токен недействителен или пользователь удален.
    """
    if session_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не авторизован",
        )

    try:
        payload = decode_session_token(session_token)
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError, jwt.PyJWTError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительная сессия",
        ) from exc

    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    return user
