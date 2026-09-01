"""Совместимые команды старого core-модуля запросов."""

from app.db.base import Base
from app.db.seed import seed_reference_data
from app.db.session import async_engine, async_session_factory, sync_engine, sync_session_factory


async def create_tables_async() -> None:
    """Создает таблицы через metadata для старого dev-сценария.

    Новый production-путь должен использовать Alembic.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


def create_exercises_values_sync() -> None:
    """Загружает справочные данные через новую seed-команду."""
    with sync_session_factory() as session:
        seed_reference_data(session)
