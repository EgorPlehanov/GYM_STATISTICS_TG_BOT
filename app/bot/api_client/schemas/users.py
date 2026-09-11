"""DTO-схемы API-клиента Telegram-бота для пользователей."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnsureUserResult:
    """Результат регистрации пользователя через internal API.

    Attributes:
        created: признак того, что пользователь был создан в текущем запросе.
    """

    created: bool
