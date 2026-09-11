"""DTO-схемы API-клиента Telegram-бота для упражнений."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BotExercise:
    """Упражнение, полученное ботом через backend API.

    Attributes:
        id: внутренний id упражнения из справочника.
        name: название упражнения для кнопок и inline-результатов.
        description: описание упражнения для inline-подсказки.
    """

    id: int
    name: str
    description: str | None
