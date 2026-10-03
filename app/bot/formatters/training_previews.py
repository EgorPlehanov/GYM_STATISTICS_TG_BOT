"""Варианты Rich Message HTML для результата тренировки в группе."""

from dataclasses import dataclass
from enum import Enum


class RichFormat(str, Enum):
    """Синтаксис отдельного метода Bot API sendRichMessage."""

    HTML = "html"


@dataclass(frozen=True, slots=True)
class TrainingPreview:
    """Один вариант оформления сообщения о перенаправленной тренировке."""

    title: str
    text: str
    rich_format: RichFormat = RichFormat.HTML


def build_training_previews() -> tuple[TrainingPreview, ...]:
    """Возвращает варианты Rich HTML для выбора оформления редиректа."""
    return (
        TrainingPreview(
            "Редирект: акцент на результате",
            '<h6><a href="tg://user?id=409218520">Егор Плеханов</a> · Ср, 30 сентября</h6>'
            "<blockquote>Лёгкая тренировка после дороги, без дополнительного веса.</blockquote>"
            "<table bordered striped compact>"
            "<tr><td>Приседания</td><td>80×8, 85×6 × 2</td></tr>"
            "<tr><td>Румынская тяга</td><td>70×10, 75×8</td></tr>"
            "<tr><td>Выпады</td><td>18×12 × 2</td></tr>"
            "</table>"
            "<footer>3 упражнения · 7 подходов</footer>",
        ),
    )
