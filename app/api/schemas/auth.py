"""DTO-схемы авторизации."""

from pydantic import BaseModel, ConfigDict


class TelegramLoginRequest(BaseModel):
    """Данные Telegram Login Widget, которые frontend отправляет в API."""

    id: int
    first_name: str
    auth_date: int
    hash: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None


class TelegramMiniAppLoginRequest(BaseModel):
    """Raw initData Telegram Mini App, которые frontend отправляет в API."""

    init_data: str


class CurrentUserResponse(BaseModel):
    """Данные текущего авторизованного пользователя для frontend."""

    id: int
    telegram_id: int
    name: str
    language_code: str | None

    model_config = ConfigDict(from_attributes=True)
