"""Методы API-клиента Telegram-бота для упражнений."""

from app.bot.api_client.base import BotApiClientBase
from app.bot.api_client.schemas.exercises import BotExercise


class BotExercisesApiClientMixin(BotApiClientBase):
    """Методы internal API для работы Telegram-бота с упражнениями."""

    async def get_exercises(
        self,
        telegram_id: int,
        page_size: int = 50,
        page_num: int = 0,
        substring: str | None = None,
    ) -> list[BotExercise]:
        """Возвращает упражнения для выбора в Telegram-боте.

        Args:
            telegram_id: Telegram user id для пользовательской сортировки.
            page_size: размер страницы.
            page_num: номер страницы, начиная с 0.
            substring: строка поиска по справочнику упражнений.

        Returns:
            список упражнений в формате, удобном для handlers/keyboards бота.
        """
        client = self._get_client()

        params: dict[str, int | str] = {
            "telegram_id": telegram_id,
            "page_size": page_size,
            "page_num": page_num,
        }
        if substring is not None:
            params["substring"] = substring

        response = await client.get(
            "/internal/bot/exercises",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params=params,
        )
        response.raise_for_status()
        return [BotExercise(**item) for item in response.json()]

    async def get_exercise(self, exercise_id: int) -> BotExercise:
        """Возвращает одно упражнение по id через internal API.

        Args:
            exercise_id: внутренний id упражнения из справочника.

        Returns:
            упражнение, найденное backend API.
        """
        client = self._get_client()

        response = await client.get(
            f"/internal/bot/exercises/{exercise_id}",
            headers={"X-Internal-Api-Key": self.internal_api_token},
        )
        response.raise_for_status()
        return BotExercise(**response.json())
