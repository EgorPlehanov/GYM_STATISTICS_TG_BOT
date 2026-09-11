"""DTO-схемы internal API для минимальной Telegram admin-панели."""

from pydantic import BaseModel


class InternalBotAdminAccessResponse(BaseModel):
    """Результат проверки доступа к Telegram admin-панели.

    Attributes:
        has_access: признак доступа к admin-панели.
        roles: коды ролей пользователя.
    """

    has_access: bool
    roles: list[str]


class InternalBotAdminStatusResponse(BaseModel):
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
