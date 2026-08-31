"""Точка входа для подключения к базе данных.

Сейчас настройка сессий находится в старом модуле `db.database`.
Она будет перенесена сюда на этапе рефакторинга слоя базы данных.
"""

from db.database import (
    async_engine,
    async_session_factory,
    sync_engine,
    sync_session_factory,
)

__all__ = [
    "async_engine",
    "async_session_factory",
    "sync_engine",
    "sync_session_factory",
]
