"""Методы API-клиента Telegram-бота для статистики."""

from app.bot.api_client.base import BotApiClientBase
from app.bot.api_client.schemas.statistics import BotExerciseRating
from app.core.weights import normalize_weight


class BotStatisticsApiClientMixin(BotApiClientBase):
    """Методы internal API для статистики Telegram-бота."""

    async def get_user_exercise_rating(self, telegram_id: int) -> list[BotExerciseRating]:
        """Возвращает рейтинг упражнений пользователя через internal API.

        Args:
            telegram_id: Telegram user id пользователя.

        Returns:
            список рейтингов упражнений для вывода в команде `/statistics`.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/statistics/exercise-rating",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={"telegram_id": telegram_id},
        )
        response.raise_for_status()
        return [
            BotExerciseRating(
                **{**item, "rating_value": normalize_weight(item["rating_value"])}
            )
            for item in response.json()
        ]
