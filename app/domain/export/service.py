"""Сервис экспорта данных."""


from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import export as export_repository


class ExportService:
    """Бизнес-сценарии для экспорта данных."""

    get_export_data = staticmethod(export_repository.get_export_data)


ExportData = export_repository.ExportData


async def get_export_data(session: AsyncSession, user_id: int) -> list[ExportData]:
    """Возвращает набор данных для экспорта тренировок пользователя."""
    return await export_repository.get_export_data(session, user_id)
