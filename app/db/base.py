"""Базовые типы и metadata SQLAlchemy."""

from typing import Annotated

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase


str_256 = Annotated[str, 256]
str_2048 = Annotated[str, 2048]


class Base(DeclarativeBase):
    """Базовый класс SQLAlchemy-моделей проекта."""

    type_annotation_map = {
        str_256: String(256),
        str_2048: String(2048),
    }

__all__ = ["Base", "str_256", "str_2048"]
