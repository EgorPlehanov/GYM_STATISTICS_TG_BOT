"""Router служебного internal API."""

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_internal_service
from app.api.schemas.internal_bot import (
    InternalBotUserEnsureRequest,
    InternalBotUserEnsureResponse,
)
from app.domain.users.service import create_user_if_not_exists

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(get_internal_service)],
)


@router.get("/health")
async def internal_health_check() -> dict[str, str]:
    """Проверяет service-to-service авторизацию internal API.

    Выход:
        короткий JSON-ответ без бизнес-данных.
    """
    return {"status": "ok"}


@router.post("/bot/users/ensure", response_model=InternalBotUserEnsureResponse)
async def ensure_bot_user(
    payload: InternalBotUserEnsureRequest,
    session: DbSession,
) -> InternalBotUserEnsureResponse:
    """Создает пользователя из Telegram-бота, если его еще нет.

    Вход:
        payload: Telegram user id и профильные данные из update-а бота.

    Выход:
        признак того, была ли создана новая запись пользователя.
    """
    created = await create_user_if_not_exists(
        session=session,
        user_id=payload.telegram_id,
        name=payload.name,
        language_code=payload.language_code,
    )
    return InternalBotUserEnsureResponse(created=created)
