"""DTO-схемы API-клиента Telegram-бота для групп."""

from dataclasses import dataclass


@dataclass
class BotRedirectGroup:
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


@dataclass(frozen=True)
class BotCurrentGroupRedirectToggleResult:
    """Результат переключения редиректа в текущей Telegram-группе.

    Attributes:
        is_redirect_to_group: новое состояние редиректа.
        created: признак создания новой связи пользователя с группой.
    """

    is_redirect_to_group: bool
    created: bool
