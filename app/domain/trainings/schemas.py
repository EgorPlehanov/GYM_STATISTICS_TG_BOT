"""Доменные схемы тренировок."""

from enum import Enum


class TrainingSaveOutcome(str, Enum):
    """Семантический результат сохранения тренировки.

    Значения отделяют бизнес-результат сохранения от технических признаков
    изменения строк тренировки и подходов в репозитории.
    """

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
