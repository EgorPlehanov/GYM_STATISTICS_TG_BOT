"""DTO-схемы API-клиента Telegram-бота для admin-panel."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BotAdminAccess:
    """Результат проверки доступа к Telegram admin-панели.

    Attributes:
        has_access: признак доступа к admin-панели.
        roles: коды ролей пользователя.
    """

    has_access: bool
    roles: list[str]


@dataclass(frozen=True)
class BotAdminStatus:
    """Минимальный статус backend API для Telegram admin-панели.

    Attributes:
        api_status: состояние backend API.
        app_env: текущее окружение приложения.
        has_access: признак доступа пользователя к admin-панели.
        roles: коды ролей пользователя.
    """

    api_status: str
    app_env: str
    has_access: bool
    roles: list[str]
