"""Клиент backend API для Telegram-бота."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.bot.api_client.admin import BotAdminApiClientMixin
from app.bot.api_client.exercises import BotExercisesApiClientMixin
from app.bot.api_client.export import BotExportApiClientMixin
from app.bot.api_client.schemas.admin import BotAdminAccess, BotAdminStatus
from app.bot.api_client.schemas.exercises import BotExercise
from app.bot.api_client.schemas.export import BotExportData
from app.bot.api_client.schemas.statistics import BotExerciseRating
from app.bot.api_client.schemas.users import EnsureUserResult
from app.bot.api_client.statistics import BotStatisticsApiClientMixin
from app.bot.api_client.users import BotUsersApiClientMixin

__all__ = [
    "BotAdminAccess",
    "BotAdminStatus",
    "BotApiClient",
    "BotCurrentGroupRedirectToggleResult",
    "BotExercise",
    "BotExerciseRating",
    "BotExportData",
    "BotRedirectGroup",
    "BotTrainingByDateResult",
    "BotTrainingSaveResult",
    "BotTrainingStartContext",
    "EnsureUserResult",
]


@dataclass(frozen=True)
class BotTrainingByDateResult:
    """Данные тренировки за дату, полученные через backend API.

    Attributes:
        exists: признак того, что тренировка уже была в базе.
        training_data: структура тренировки в формате FSM-сценария бота.
    """

    exists: bool
    training_data: dict[str, Any]


@dataclass(frozen=True)
class BotTrainingStartContext:
    """Стартовые данные для сценария добавления тренировки.

    Attributes:
        most_frequent_exercises: упражнения для первичной клавиатуры выбора.
        weight_repetitions_modes: подсказки веса и повторений по прошлым тренировкам.
    """

    most_frequent_exercises: list[BotExercise]
    weight_repetitions_modes: dict[int, dict[str, Any]]


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


@dataclass(frozen=True)
class BotTrainingSaveResult:
    """Результат сохранения тренировки через backend API.

    Attributes:
        training_id: внутренний id сохраненной тренировки.
        updated: признак обновления существующей тренировки.
        created: признак создания новой тренировки.
    """

    training_id: int
    updated: bool
    created: bool


class BotApiClient(
    BotUsersApiClientMixin,
    BotAdminApiClientMixin,
    BotExercisesApiClientMixin,
    BotStatisticsApiClientMixin,
    BotExportApiClientMixin,
):
    """HTTP-клиент, через который Telegram-бот обращается к backend API."""

    async def get_training_dates(self, telegram_id: int) -> list[date]:
        """Возвращает даты тренировок пользователя для календаря бота.

        Args:
            telegram_id: Telegram user id пользователя.

        Returns:
            список дат тренировок, преобразованный из JSON-строк в `date`.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/trainings/dates",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={"telegram_id": telegram_id},
        )
        response.raise_for_status()
        return [date.fromisoformat(item) for item in response.json()]

    async def get_training_start_context(
        self,
        telegram_id: int,
        page_size: int = 15,
        last_training_count: int = 12,
    ) -> BotTrainingStartContext:
        """Возвращает стартовые данные для команды `/training`.

        Args:
            telegram_id: Telegram user id пользователя.
            page_size: количество частых упражнений для первичной клавиатуры.
            last_training_count: количество последних тренировок для расчета подсказок.

        Returns:
            контекст для сохранения в FSM state перед выбором даты.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/trainings/start-context",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={
                "telegram_id": telegram_id,
                "page_size": page_size,
                "last_training_count": last_training_count,
            },
        )
        response.raise_for_status()

        payload = response.json()
        return BotTrainingStartContext(
            most_frequent_exercises=[
                BotExercise(**item) for item in payload["most_frequent_exercises"]
            ],
            weight_repetitions_modes=_restore_weight_repetitions_modes(
                payload["weight_repetitions_modes"]
            ),
        )

    async def get_training_by_date(
        self,
        telegram_id: int,
        training_date: date,
    ) -> BotTrainingByDateResult:
        """Возвращает тренировку пользователя за дату или пустую структуру.

        Args:
            telegram_id: Telegram user id пользователя.
            training_date: дата, выбранная в Telegram-боте.

        Returns:
            результат с флагом существования и FSM-структурой тренировки.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/trainings/by-date",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={
                "telegram_id": telegram_id,
                "training_date": training_date.isoformat(),
            },
        )
        response.raise_for_status()

        payload = response.json()
        return BotTrainingByDateResult(
            exists=payload["exists"],
            training_data=_deserialize_training_data(payload["training_data"]),
        )

    async def save_training(
        self,
        training_data: dict[str, Any],
    ) -> BotTrainingSaveResult:
        """Сохраняет тренировку через internal API.

        Args:
            training_data: FSM-структура тренировки бота.

        Returns:
            результат сохранения тренировки в backend API.
        """
        client = self._get_client()

        response = await client.post(
            "/internal/bot/trainings",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "training_data": _serialize_training_data(training_data),
            },
        )
        response.raise_for_status()
        return BotTrainingSaveResult(**response.json())

    async def delete_training(self, training_id: int) -> None:
        """Удаляет тренировку через internal API.

        Args:
            training_id: внутренний id тренировки.
        """
        client = self._get_client()

        response = await client.delete(
            f"/internal/bot/trainings/{training_id}",
            headers={"X-Internal-Api-Key": self.internal_api_token},
        )
        response.raise_for_status()

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

    async def create_training_result_message(
        self,
        group_id: int,
        training_id: int,
        message_id: int,
    ) -> None:
        """Создает запись о сообщении результата тренировки.

        Args:
            group_id: Telegram chat id группы.
            training_id: id сохраненной тренировки.
            message_id: Telegram message id отправленного результата.
        """
        client = self._get_client()

        response = await client.post(
            "/internal/bot/groups/training-result-messages",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "group_id": group_id,
                "training_id": training_id,
                "message_id": message_id,
            },
        )
        response.raise_for_status()

    async def update_training_result_message(
        self,
        group_id: int,
        training_id: int,
        new_message_id: int,
    ) -> bool:
        """Обновляет Telegram message id результата тренировки.

        Args:
            group_id: Telegram chat id группы.
            training_id: id сохраненной тренировки.
            new_message_id: новый Telegram message id после повторной отправки.

        Returns:
            признак того, что существующая запись была найдена и обновлена.
        """
        client = self._get_client()

        response = await client.patch(
            "/internal/bot/groups/training-result-messages",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "group_id": group_id,
                "training_id": training_id,
                "new_message_id": new_message_id,
            },
        )
        response.raise_for_status()
        return response.json()["updated"]

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


def _serialize_training_data(training_data: dict[str, Any]) -> dict[str, Any]:
    """Готовит FSM-структуру тренировки к отправке через JSON.

    Args:
        training_data: структура с `date`, `datetime` в подходах и числовыми ключами.

    Returns:
        JSON-совместимый словарь с ISO-датой тренировки, ISO-временем подходов и строковыми ключами.
    """
    serialized = dict(training_data)
    if isinstance(serialized.get("date"), datetime):
        serialized["date"] = serialized["date"].date().isoformat()
    elif isinstance(serialized.get("date"), date):
        serialized["date"] = serialized["date"].isoformat()

    exercises = {}
    for exercise_id, exercise_data in serialized.get("exercises", {}).items():
        exercise = dict(exercise_data)
        exercise["sets"] = {
            str(set_id): _serialize_set_data(set_data)
            for set_id, set_data in exercise.get("sets", {}).items()
        }
        exercises[str(exercise_id)] = exercise

    serialized["exercises"] = exercises
    return serialized


def _serialize_set_data(set_data: dict[str, Any]) -> dict[str, Any]:
    """Готовит данные подхода к отправке через JSON."""
    serialized = dict(set_data)
    if isinstance(serialized.get("time"), datetime):
        serialized["time"] = serialized["time"].isoformat()
    return serialized


def _deserialize_training_data(training_data: dict[str, Any]) -> dict[str, Any]:
    """Восстанавливает FSM-структуру тренировки после передачи через JSON.

    Args:
        training_data: JSON-словарь, полученный от internal API.

    Returns:
        структура тренировки с `date`, `datetime` в подходах и числовыми ключами.
    """
    restored = dict(training_data)
    if restored.get("date") is not None:
        restored["date"] = date.fromisoformat(restored["date"])

    exercises = {}
    for exercise_id, exercise_data in restored.get("exercises", {}).items():
        exercise = dict(exercise_data)
        exercise["sets"] = {
            int(set_id): _deserialize_set_data(set_data)
            for set_id, set_data in exercise.get("sets", {}).items()
        }
        exercises[int(exercise_id)] = exercise

    restored["exercises"] = exercises
    return restored


def _deserialize_set_data(set_data: dict[str, Any]) -> dict[str, Any]:
    """Восстанавливает данные подхода после передачи через JSON."""
    restored = dict(set_data)
    if restored.get("time") is not None:
        restored["time"] = datetime.fromisoformat(restored["time"])
    return restored


def _restore_weight_repetitions_modes(
    weight_repetitions_modes: dict[str, Any],
) -> dict[int, dict[str, Any]]:
    """Восстанавливает числовые ключи подсказок после JSON.

    Args:
        weight_repetitions_modes: JSON-словарь подсказок с ключами-строками.

    Returns:
        словарь с `int` ключами упражнений и подходов для старых FSM-утилит.
    """
    restored = {}
    for exercise_id, exercise_mode in weight_repetitions_modes.items():
        restored[int(exercise_id)] = {
            **exercise_mode,
            "sets_modes": {
                int(set_id): set_mode
                for set_id, set_mode in exercise_mode.get("sets_modes", {}).items()
            },
        }
    return restored
