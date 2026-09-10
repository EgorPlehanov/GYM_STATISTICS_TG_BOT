"""Internal endpoints экспорта данных для Telegram-бота."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.schemas.internal.export import InternalBotExportDataResponse
from app.domain.export.service import get_export_data

router = APIRouter()


@router.get("/bot/export/data", response_model=list[InternalBotExportDataResponse])
async def get_bot_export_data(
    session: DbSession,
    telegram_id: int,
) -> list[InternalBotExportDataResponse]:
    """Возвращает данные экспорта тренировок пользователя для Telegram-бота.

    Args:
        telegram_id: Telegram user id пользователя.

    Returns:
        строки данных, из которых bot adapter собирает XLSX-файл.
    """
    return await get_export_data(session=session, user_id=telegram_id)
