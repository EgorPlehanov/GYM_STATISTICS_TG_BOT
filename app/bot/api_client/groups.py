"""Методы API-клиента Telegram-бота для групп."""

from app.bot.api_client.base import BotApiClientBase
from app.bot.api_client.schemas.groups import (
    BotCurrentGroupRedirectToggleResult,
    BotRedirectGroup,
)


class BotGroupsApiClientMixin(BotApiClientBase):
    """Методы internal API для работы Telegram-бота с группами."""

    async def get_redirect_group_ids(self, telegram_id: int) -> list[int]:
        """Возвращает группы, куда нужно отправить результат тренировки.

        Args:
            telegram_id: Telegram user id пользователя.

        Returns:
            список Telegram chat id групп с включенным редиректом результата.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/groups/redirect-targets",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={"telegram_id": telegram_id},
        )
        response.raise_for_status()
        return list(response.json())

    async def ensure_group(
        self,
        group_id: int,
        group_name: str,
        group_type: str,
    ) -> bool:
        """Создает Telegram-группу или восстанавливает ее доступность для бота.

        Args:
            group_id: Telegram chat id группы.
            group_name: название группы.
            group_type: тип Telegram-чата.

        Returns:
            признак того, что группа была создана в текущем запросе.
        """
        client = self._get_client()

        response = await client.post(
            "/internal/bot/groups/ensure",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "group_id": group_id,
                "group_name": group_name,
                "group_type": group_type,
            },
        )
        response.raise_for_status()
        return response.json()["created"]

    async def get_redirect_groups(self, telegram_id: int) -> list[BotRedirectGroup]:
        """Возвращает группы пользователя для меню настройки редиректа.

        Args:
            telegram_id: Telegram user id пользователя.

        Returns:
            список групп, доступных для настройки редиректа.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/groups/redirect-settings",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={"telegram_id": telegram_id},
        )
        response.raise_for_status()
        return [BotRedirectGroup(**item) for item in response.json()]

    async def toggle_current_group_redirect(
        self,
        telegram_id: int,
        group_id: int,
        group_name: str,
        group_type: str,
        is_user_admin: bool,
    ) -> BotCurrentGroupRedirectToggleResult:
        """Переключает редирект результата тренировки в текущей группе.

        Args:
            telegram_id: Telegram user id пользователя.
            group_id: Telegram chat id группы.
            group_name: название группы.
            group_type: тип Telegram-чата.
            is_user_admin: признак администратора группы у пользователя.

        Returns:
            новое состояние редиректа и признак создания связи пользователя с группой.
        """
        client = self._get_client()

        response = await client.post(
            "/internal/bot/groups/redirect-settings/toggle-current",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "telegram_id": telegram_id,
                "group_id": group_id,
                "group_name": group_name,
                "group_type": group_type,
                "is_user_admin": is_user_admin,
            },
        )
        response.raise_for_status()
        return BotCurrentGroupRedirectToggleResult(**response.json())

    async def update_redirect_group(
        self,
        telegram_id: int,
        group_id: int,
        is_redirect_to_group: bool,
    ) -> None:
        """Обновляет состояние редиректа пользователя в выбранную группу.

        Args:
            telegram_id: Telegram user id пользователя.
            group_id: Telegram chat id группы.
            is_redirect_to_group: новое состояние редиректа.
        """
        client = self._get_client()

        response = await client.patch(
            "/internal/bot/groups/redirect-settings",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "telegram_id": telegram_id,
                "group_id": group_id,
                "is_redirect_to_group": is_redirect_to_group,
            },
        )
        response.raise_for_status()

    async def get_training_result_message_id(
        self,
        group_id: int,
        training_id: int,
    ) -> int | None:
        """Возвращает Telegram message id результата тренировки в группе.

        Args:
            group_id: Telegram chat id группы.
            training_id: id сохраненной тренировки.

        Returns:
            Telegram message id или `None`, если запись не найдена.
        """
        client = self._get_client()

        response = await client.get(
            f"/internal/bot/groups/{group_id}/training-results/{training_id}/message",
            headers={"X-Internal-Api-Key": self.internal_api_token},
        )
        response.raise_for_status()
        return response.json()["message_id"]

    async def upsert_training_result_message(
        self,
        group_id: int,
        training_id: int,
        message_id: int,
    ) -> None:
        """Сохраняет актуальный Telegram message id результата тренировки.

        Args:
            group_id: Telegram chat id группы.
            training_id: id сохраненной тренировки.
            message_id: Telegram message id отправленного результата.
        """
        client = self._get_client()

        response = await client.put(
            "/internal/bot/groups/training-result-messages",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "group_id": group_id,
                "training_id": training_id,
                "message_id": message_id,
            },
        )
        response.raise_for_status()

    async def update_group_bot_banned(
        self,
        group_id: int,
        is_bot_banned: bool,
    ) -> None:
        """Обновляет признак недоступности группы для Telegram-бота.

        Args:
            group_id: Telegram chat id группы.
            is_bot_banned: признак того, что бот удален или заблокирован в группе.
        """
        client = self._get_client()

        response = await client.patch(
            f"/internal/bot/groups/{group_id}/bot-banned",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={"is_bot_banned": is_bot_banned},
        )
        response.raise_for_status()

    async def update_group_bot_admin(
        self,
        group_id: int,
        is_bot_admin: bool,
    ) -> None:
        """Обновляет признак администратора у Telegram-бота в группе.

        Args:
            group_id: Telegram chat id группы.
            is_bot_admin: признак того, что бот является администратором группы.
        """
        client = self._get_client()

        response = await client.patch(
            f"/internal/bot/groups/{group_id}/bot-admin",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={"is_bot_admin": is_bot_admin},
        )
        response.raise_for_status()

    async def delete_group_user(
        self,
        group_id: int,
        telegram_id: int,
    ) -> None:
        """Удаляет связь пользователя с Telegram-группой.

        Args:
            group_id: Telegram chat id группы.
            telegram_id: Telegram user id пользователя.
        """
        client = self._get_client()

        response = await client.delete(
            f"/internal/bot/groups/{group_id}/users/{telegram_id}",
            headers={"X-Internal-Api-Key": self.internal_api_token},
        )
        response.raise_for_status()

    async def update_group_user_admin(
        self,
        group_id: int,
        telegram_id: int,
        is_admin: bool,
    ) -> None:
        """Обновляет признак администратора пользователя в Telegram-группе.

        Args:
            group_id: Telegram chat id группы.
            telegram_id: Telegram user id пользователя.
            is_admin: признак того, что пользователь является администратором группы.
        """
        client = self._get_client()

        response = await client.patch(
            f"/internal/bot/groups/{group_id}/users/{telegram_id}/admin",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={"is_admin": is_admin},
        )
        response.raise_for_status()

    async def migrate_group_to_supergroup(
        self,
        group_id: int,
        supergroup_id: int,
        supergroup_name: str,
        supergroup_type: str,
    ) -> None:
        """Переносит связи старой Telegram-группы на новую супергруппу.

        Args:
            group_id: старый Telegram chat id группы.
            supergroup_id: новый Telegram chat id супергруппы.
            supergroup_name: название супергруппы.
            supergroup_type: тип Telegram-чата после миграции.
        """
        client = self._get_client()

        response = await client.patch(
            "/internal/bot/groups/migrate-to-supergroup",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "group_id": group_id,
                "supergroup_id": supergroup_id,
                "supergroup_name": supergroup_name,
                "supergroup_type": supergroup_type,
            },
        )
        response.raise_for_status()
