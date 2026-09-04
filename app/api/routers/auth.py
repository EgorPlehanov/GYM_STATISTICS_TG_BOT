"""Router авторизации."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.api.schemas.auth import CurrentUserResponse, TelegramLoginRequest
from app.core.config import config
from app.core.security import create_session_token
from app.db.models import User
from app.domain.auth.service import TelegramLoginData, authenticate_telegram_login

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

    Вход:
        payload: подписанные данные Telegram Login Widget.

    Выход:
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

    session_token = create_session_token(
        user_id=user.id,
        telegram_id=user.telegram_id,
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
    return user


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
