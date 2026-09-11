"""DTO-схемы internal API для Telegram-групп."""

from pydantic import BaseModel, ConfigDict


class InternalBotRedirectGroupResponse(BaseModel):
    """Группа пользователя, доступная для настройки редиректа.

    Attributes:
        id: внутренний id связи пользователя и группы.
        group_id: Telegram chat id группы.
        group_name: название группы.
        is_redirect_to_group: признак включенного редиректа в группу.
    """

    id: int
    group_id: int
    group_name: str
    is_redirect_to_group: bool

    model_config = ConfigDict(from_attributes=True)


class InternalBotCurrentGroupRedirectToggleRequest(BaseModel):
    """Данные для переключения редиректа в текущей Telegram-группе.

    Attributes:
        telegram_id: Telegram user id пользователя.
        group_id: Telegram chat id группы.
        group_name: название группы.
        group_type: тип Telegram-чата.
        is_user_admin: признак администратора группы у пользователя.
    """

    telegram_id: int
    group_id: int
    group_name: str
    group_type: str
    is_user_admin: bool


class InternalBotCurrentGroupRedirectToggleResponse(BaseModel):
    """Результат переключения редиректа в текущей Telegram-группе.

    Attributes:
        is_redirect_to_group: новое состояние редиректа.
        created: признак создания новой связи пользователя с группой.
    """

    is_redirect_to_group: bool
    created: bool


class InternalBotRedirectGroupUpdateRequest(BaseModel):
    """Данные для обновления редиректа пользователя в группу.

    Attributes:
        telegram_id: Telegram user id пользователя.
        group_id: Telegram chat id группы.
        is_redirect_to_group: новое состояние редиректа.
    """

    telegram_id: int
    group_id: int
    is_redirect_to_group: bool


class InternalBotTrainingResultMessageCreateRequest(BaseModel):
    """Данные для создания записи о сообщении результата тренировки.

    Attributes:
        group_id: Telegram chat id группы.
        training_id: id сохраненной тренировки.
        message_id: Telegram message id отправленного результата.
    """

    group_id: int
    training_id: int
    message_id: int


class InternalBotTrainingResultMessageUpdateRequest(BaseModel):
    """Данные для обновления Telegram message id результата тренировки.

    Attributes:
        group_id: Telegram chat id группы.
        training_id: id сохраненной тренировки.
        new_message_id: новый Telegram message id после повторной отправки.
    """

    group_id: int
    training_id: int
    new_message_id: int


class InternalBotTrainingResultMessageUpdateResponse(BaseModel):
    """Результат обновления записи о сообщении результата тренировки.

    Attributes:
        updated: признак того, что существующая запись была найдена и обновлена.
    """

    updated: bool


class InternalBotGroupBotBannedRequest(BaseModel):
    """Данные для обновления признака недоступности группы для бота.

    Attributes:
        is_bot_banned: признак того, что бот удален или заблокирован в группе.
    """

    is_bot_banned: bool


class InternalBotGroupEnsureRequest(BaseModel):
    """Данные Telegram-группы, которую нужно создать или восстановить.

    Attributes:
        group_id: Telegram chat id группы.
        group_name: название группы.
        group_type: тип Telegram-чата.
    """

    group_id: int
    group_name: str
    group_type: str


class InternalBotGroupEnsureResponse(BaseModel):
    """Результат создания или восстановления Telegram-группы.

    Attributes:
        created: признак того, что группа была создана в текущем запросе.
    """

    created: bool


class InternalBotGroupBotAdminRequest(BaseModel):
    """Данные для обновления признака администратора у Telegram-бота.

    Attributes:
        is_bot_admin: признак того, что бот является администратором группы.
    """

    is_bot_admin: bool


class InternalBotGroupMigrateToSupergroupRequest(BaseModel):
    """Данные для переноса старой группы в новую супергруппу.

    Attributes:
        group_id: старый Telegram chat id группы.
        supergroup_id: новый Telegram chat id супергруппы.
        supergroup_name: название супергруппы.
        supergroup_type: тип Telegram-чата после миграции.
    """

    group_id: int
    supergroup_id: int
    supergroup_name: str
    supergroup_type: str


class InternalBotGroupUserAdminRequest(BaseModel):
    """Данные для обновления признака администратора пользователя в группе.

    Attributes:
        is_admin: признак того, что пользователь является администратором группы.
    """

    is_admin: bool
