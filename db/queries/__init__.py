"""Совместимый экспорт старого пакета запросов.

Новый код должен импортировать функции из `app.db.repositories`.
"""

from app.db.repositories import *  # noqa: F401,F403
