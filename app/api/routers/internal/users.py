"""Internal endpoints для сценариев пользователей Telegram-бота."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.schemas.internal.users import (
    InternalBotUserEnsureRequest,
    InternalBotUserEnsureResponse,
    InternalBotUserPrivateChatBannedRequest,
)
from app.domain.users.service import create_user_if_not_exists, update_user_private_chat_banned

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


@router.patch("/bot/users/{telegram_id}/private-chat-banned")
async def update_bot_user_private_chat_banned(
    telegram_id: int,
    payload: InternalBotUserPrivateChatBannedRequest,
    session: DbSession,
) -> dict[str, str]:
    """Обновляет признак блокировки бота пользователем в личном чате.

    Args:
        telegram_id: Telegram user id пользователя.
        payload: новое состояние блокировки.

    Returns:
        короткий статус успешного выполнения операции.
    """
    await update_user_private_chat_banned(
        session=session,
        user_id=telegram_id,
        is_private_chat_banned=payload.is_private_chat_banned,
    )
    return {"status": "ok"}
