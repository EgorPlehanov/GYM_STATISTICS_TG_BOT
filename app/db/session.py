"""Подключение к базе данных и фабрики SQLAlchemy-сессий."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import config

sync_engine = create_engine(
    url=config.DB_URL_SYNC,
)

async_engine = create_async_engine(
    url=config.DB_URL_ASYNC,
)

sync_session_factory = sessionmaker(sync_engine)
async_session_factory = async_sessionmaker(async_engine)

__all__ = [
    "async_engine",
    "async_session_factory",
    "sync_engine",
    "sync_session_factory",
]
