"""Internal endpoints для минимальной Telegram admin-панели."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.schemas.internal.admin import (
    InternalBotAdminAccessResponse,
    InternalBotAdminStatusResponse,
)
from app.core.config import config
from app.domain.users.service import get_user_role_codes_by_telegram_id

router = APIRouter()

ADMIN_ROLE_CODES = {"owner", "admin"}


@router.get("/bot/admin/access", response_model=InternalBotAdminAccessResponse)
async def get_bot_admin_access(
    session: DbSession,
    telegram_id: int,
) -> InternalBotAdminAccessResponse:
    """Проверяет доступ пользователя к Telegram admin-панели.

    Args:
        telegram_id: Telegram user id пользователя.

    Returns:
        признак доступа и список ролей пользователя.
    """
    roles = await get_user_role_codes_by_telegram_id(session, telegram_id)
    return InternalBotAdminAccessResponse(
        has_access=bool(ADMIN_ROLE_CODES.intersection(roles)),
        roles=roles,
    )


@router.get("/bot/admin/status", response_model=InternalBotAdminStatusResponse)
async def get_bot_admin_status(
    session: DbSession,
    telegram_id: int,
) -> InternalBotAdminStatusResponse:
    """Возвращает безопасный статус системы для Telegram admin-панели.

    Args:
        telegram_id: Telegram user id пользователя.

    Returns:
        краткий статус backend API, окружение и роли пользователя.
    """
    roles = await get_user_role_codes_by_telegram_id(session, telegram_id)
    has_access = bool(ADMIN_ROLE_CODES.intersection(roles))
    return InternalBotAdminStatusResponse(
        api_status="ok",
        app_env=config.APP_ENV,
        has_access=has_access,
        roles=roles,
    )
