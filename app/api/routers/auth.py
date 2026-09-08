"""Router авторизации."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.api.schemas.auth import (
    CurrentUserResponse,
    TelegramLoginRequest,
    TelegramMiniAppLoginRequest,
)
from app.core.config import config
from app.core.security import create_session_token
from app.db.models import User
from app.domain.auth.service import (
    TelegramLoginData,
    authenticate_telegram_login,
    authenticate_telegram_mini_app,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/telegram-login", response_model=CurrentUserResponse)
async def telegram_login(
    payload: TelegramLoginRequest,
    response: Response,
    session: DbSession,
) -> User:
    """Авторизует пользователя через Telegram Login Widget и устанавливает cookie.

    Args:
        payload: подписанные данные Telegram Login Widget.

    Returns:
        текущий пользователь приложения.
    """
    try:
        user = await authenticate_telegram_login(
            session=session,
            login_data=TelegramLoginData(**payload.model_dump()),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    set_session_cookie(response, user)
    return user


@router.post("/telegram-mini-app", response_model=CurrentUserResponse)
async def telegram_mini_app_login(
    payload: TelegramMiniAppLoginRequest,
    response: Response,
    session: DbSession,
) -> User:
    """Авторизует пользователя через Telegram Mini App initData и устанавливает cookie.

    Args:
        payload: raw `Telegram.WebApp.initData`, полученный frontend внутри Telegram.

    Returns:
        текущий пользователь приложения.
    """
    try:
        user = await authenticate_telegram_mini_app(
            session=session,
            init_data=payload.init_data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    set_session_cookie(response, user)
    return user


def set_session_cookie(response: Response, user: User) -> None:
    """Устанавливает `httpOnly` cookie web-сессии для авторизованного пользователя."""
    session_token = create_session_token(
        user_id=user.id,
    )
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=session_token,
        max_age=config.SESSION_TTL_SECONDS,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite=config.COOKIE_SAMESITE,
        domain=config.COOKIE_DOMAIN,
    )


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: CurrentUser) -> User:
    """Возвращает текущего авторизованного пользователя."""
    return current_user


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """Удаляет cookie web-сессии пользователя."""
    response.delete_cookie(
        key=config.SESSION_COOKIE_NAME,
        domain=config.COOKIE_DOMAIN,
        secure=config.COOKIE_SECURE,
        samesite=config.COOKIE_SAMESITE,
    )
    return {"status": "ok"}
