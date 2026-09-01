"""Совместимый импорт database layer для старого кода.

Новый код должен импортировать `app.db.session` и `app.db.base`.
"""

from app.db.base import Base, str_2048, str_256
from app.db.session import (
    async_engine,
    async_session_factory,
    sync_engine,
    sync_session_factory,
)

__all__ = [
    "Base",
    "str_256",
    "str_2048",
    "async_engine",
    "async_session_factory",
    "sync_engine",
    "sync_session_factory",
]
