"""Internal endpoints для сценариев пользователей Telegram-бота."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.schemas.internal_bot import (
    InternalBotUserEnsureRequest,
    InternalBotUserEnsureResponse,
)
from app.domain.users.service import create_user_if_not_exists

router = APIRouter()


@router.post("/bot/users/ensure", response_model=InternalBotUserEnsureResponse)
async def ensure_bot_user(
    payload: InternalBotUserEnsureRequest,
    session: DbSession,
) -> InternalBotUserEnsureResponse:
    """Создает пользователя из Telegram-бота, если его еще нет.

    Args:
        payload: Telegram user id и профильные данные из update-а бота.

    Returns:
        признак того, была ли создана новая запись пользователя.
    """
    created = await create_user_if_not_exists(
        session=session,
        user_id=payload.telegram_id,
        name=payload.name,
        language_code=payload.language_code,
    )
    return InternalBotUserEnsureResponse(created=created)
