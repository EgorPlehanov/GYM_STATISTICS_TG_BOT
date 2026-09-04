"""Зависимости FastAPI."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Возвращает асинхронную DB-сессию для одного HTTP-запроса.

    Выход:
        `AsyncSession`, которая автоматически закрывается после обработки запроса.
    """
    async with async_session_factory() as session:
        yield session
