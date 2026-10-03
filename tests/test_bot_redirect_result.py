"""Тесты редиректа результата тренировки в Telegram-группы."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import DeleteMessage, SendRichMessage
from aiogram.types import InputRichMessage

from app.bot.api_client.schemas.trainings import (
    BotDeletedRedirectMessage,
    BotTrainingSaveOutcome,
)
from app.bot.telegram.message_operations import ControlledMessageOperationResult

RICH_MESSAGE = InputRichMessage(html="<h6>Результат</h6>")


class FakeBotApiClient:
    """Заглушка internal API-клиента для проверки redirect-сценария."""

    def __init__(self, message_id: int | None = 42) -> None:
        """Создает заглушку с одной доступной redirect-группой."""
        self.get_redirect_group_ids = AsyncMock(return_value=[-1001])
        self.get_training_result_message_id = AsyncMock(return_value=message_id)
        self.upsert_training_result_message = AsyncMock()
        self.update_group_bot_banned = AsyncMock()

    async def __aenter__(self) -> "FakeBotApiClient":
        """Возвращает клиента для async context manager."""
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        """Завершает async context manager без дополнительных действий."""


def _patch_api_client(monkeypatch, api_client: FakeBotApiClient) -> None:
    """Подменяет фабрику API-клиента подготовленной заглушкой."""
    from app.bot.handlers.training_units import redirect_result

    monkeypatch.setattr(redirect_result, "BotApiClient", lambda: api_client)


async def test_unchanged_training_skips_redirect_calls(monkeypatch) -> None:
    """Проверяет отсутствие вызовов при сохранении без изменений."""
    from app.bot.handlers.training_units.redirect_result import (
        send_training_result_to_redirect_groups,
    )

    api_client = FakeBotApiClient()
    _patch_api_client(monkeypatch, api_client)
    bot = SimpleNamespace(send_rich_message=AsyncMock())

    await send_training_result_to_redirect_groups(
        bot=bot,
        rich_message=RICH_MESSAGE,
        telegram_id=1,
        training_id=10,
        outcome=BotTrainingSaveOutcome.UNCHANGED,
    )

    api_client.get_redirect_group_ids.assert_not_awaited()
    bot.send_rich_message.assert_not_awaited()


async def test_removed_training_deletes_redirect_message() -> None:
    """После удаления тренировки удаляется связанное сообщение группы."""
    from app.bot.handlers.training_units.redirect_result import (
        delete_removed_training_redirect_messages,
    )

    bot = SimpleNamespace(delete_message=AsyncMock())

    await delete_removed_training_redirect_messages(
        bot=bot,
        deleted_redirect_messages=[BotDeletedRedirectMessage(group_id=-1001, message_id=42)],
    )

    bot.delete_message.assert_awaited_once_with(chat_id=-1001, message_id=42)


@pytest.mark.parametrize(
    "operation_result",
    [
        ControlledMessageOperationResult.MESSAGE_UNAVAILABLE,
        ControlledMessageOperationResult.NOT_DELETABLE,
    ],
)
async def test_removed_training_ignores_unavailable_redirect_message(
    monkeypatch,
    operation_result: ControlledMessageOperationResult,
) -> None:
    """Недоступное для удаления сообщение не мешает завершить очистку тренировки."""
    from app.bot.handlers.training_units import redirect_result

    delete_message = AsyncMock(
        return_value=operation_result
    )
    monkeypatch.setattr(redirect_result, "delete_controlled_message", delete_message)
    bot = SimpleNamespace(delete_message=AsyncMock())

    await redirect_result.delete_removed_training_redirect_messages(
        bot=bot,
        deleted_redirect_messages=[BotDeletedRedirectMessage(group_id=-1001, message_id=42)],
    )

    delete_message.assert_awaited_once_with(bot=bot, chat_id=-1001, message_id=42)


async def test_removed_training_marks_forbidden_redirect_group(monkeypatch) -> None:
    """Недоступная группа помечается, если удалить ее сообщение невозможно."""
    from app.bot.handlers.training_units import redirect_result

    api_client = FakeBotApiClient()
    _patch_api_client(monkeypatch, api_client)
    monkeypatch.setattr(
        redirect_result,
        "delete_controlled_message",
        AsyncMock(
            side_effect=TelegramForbiddenError(
                method=DeleteMessage(chat_id=-1001, message_id=42),
                message="Forbidden: bot was kicked from the group chat",
            )
        ),
    )

    await redirect_result.delete_removed_training_redirect_messages(
        bot=SimpleNamespace(delete_message=AsyncMock()),
        deleted_redirect_messages=[BotDeletedRedirectMessage(group_id=-1001, message_id=42)],
    )

    api_client.update_group_bot_banned.assert_awaited_once_with(
        group_id=-1001,
        is_bot_banned=True,
    )


async def test_created_training_sends_and_upserts_result(monkeypatch) -> None:
    """Проверяет создание сообщения результата и единственный upsert связи."""
    from app.bot.handlers.training_units.redirect_result import (
        send_training_result_to_redirect_groups,
    )

    api_client = FakeBotApiClient()
    _patch_api_client(monkeypatch, api_client)
    bot = SimpleNamespace(send_rich_message=AsyncMock(return_value=SimpleNamespace(message_id=77)))

    await send_training_result_to_redirect_groups(
        bot=bot,
        rich_message=RICH_MESSAGE,
        telegram_id=1,
        training_id=10,
        outcome=BotTrainingSaveOutcome.CREATED,
    )

    bot.send_rich_message.assert_awaited_once_with(
        chat_id=-1001,
        rich_message=RICH_MESSAGE,
    )
    api_client.get_training_result_message_id.assert_not_awaited()
    api_client.upsert_training_result_message.assert_awaited_once_with(
        group_id=-1001,
        training_id=10,
        message_id=77,
    )


async def test_updated_training_without_message_sends_and_upserts_result(monkeypatch) -> None:
    """Проверяет восстановление результата без сохраненного Telegram message id."""
    from app.bot.handlers.training_units.redirect_result import (
        send_training_result_to_redirect_groups,
    )

    api_client = FakeBotApiClient(message_id=None)
    _patch_api_client(monkeypatch, api_client)
    bot = SimpleNamespace(send_rich_message=AsyncMock(return_value=SimpleNamespace(message_id=77)))

    await send_training_result_to_redirect_groups(
        bot=bot,
        rich_message=RICH_MESSAGE,
        telegram_id=1,
        training_id=10,
        outcome=BotTrainingSaveOutcome.UPDATED,
    )

    bot.send_rich_message.assert_awaited_once_with(
        chat_id=-1001,
        rich_message=RICH_MESSAGE,
    )
    api_client.upsert_training_result_message.assert_awaited_once()


@pytest.mark.parametrize(
    "operation_result",
    [
        ControlledMessageOperationResult.APPLIED,
        ControlledMessageOperationResult.NOT_MODIFIED,
    ],
)
async def test_updated_training_keeps_existing_message_when_edit_is_safe(
    monkeypatch,
    operation_result: ControlledMessageOperationResult,
) -> None:
    """Проверяет отсутствие повторной отправки после безопасного edit-результата."""
    from app.bot.handlers.training_units import redirect_result

    api_client = FakeBotApiClient(message_id=42)
    _patch_api_client(monkeypatch, api_client)
    edit_message = AsyncMock(return_value=operation_result)
    monkeypatch.setattr(redirect_result, "edit_controlled_rich_message", edit_message)
    bot = SimpleNamespace(send_rich_message=AsyncMock())

    await redirect_result.send_training_result_to_redirect_groups(
        bot=bot,
        rich_message=RICH_MESSAGE,
        telegram_id=1,
        training_id=10,
        outcome=BotTrainingSaveOutcome.UPDATED,
    )

    edit_message.assert_awaited_once_with(
        bot=bot,
        chat_id=-1001,
        message_id=42,
        rich_message=RICH_MESSAGE,
    )
    bot.send_rich_message.assert_not_awaited()
    api_client.upsert_training_result_message.assert_not_awaited()


async def test_updated_training_restores_unavailable_message(monkeypatch) -> None:
    """Проверяет отправку нового результата после подтвержденной потери сообщения."""
    from app.bot.handlers.training_units import redirect_result

    api_client = FakeBotApiClient(message_id=42)
    _patch_api_client(monkeypatch, api_client)
    monkeypatch.setattr(
        redirect_result,
        "edit_controlled_rich_message",
        AsyncMock(return_value=ControlledMessageOperationResult.MESSAGE_UNAVAILABLE),
    )
    bot = SimpleNamespace(send_rich_message=AsyncMock(return_value=SimpleNamespace(message_id=77)))

    await redirect_result.send_training_result_to_redirect_groups(
        bot=bot,
        rich_message=RICH_MESSAGE,
        telegram_id=1,
        training_id=10,
        outcome=BotTrainingSaveOutcome.UPDATED,
    )

    bot.send_rich_message.assert_awaited_once_with(
        chat_id=-1001,
        rich_message=RICH_MESSAGE,
    )
    api_client.upsert_training_result_message.assert_awaited_once_with(
        group_id=-1001,
        training_id=10,
        message_id=77,
    )


async def test_forbidden_group_is_marked_as_unavailable(monkeypatch) -> None:
    """Проверяет маркировку группы при запрете Telegram на отправку сообщения."""
    from app.bot.handlers.training_units.redirect_result import (
        send_training_result_to_redirect_groups,
    )

    api_client = FakeBotApiClient()
    _patch_api_client(monkeypatch, api_client)
    bot = SimpleNamespace(
        send_rich_message=AsyncMock(
            side_effect=TelegramForbiddenError(
                method=SendRichMessage(chat_id=-1001, rich_message=RICH_MESSAGE),
                message="Forbidden: bot was kicked from the group chat",
            )
        )
    )

    await send_training_result_to_redirect_groups(
        bot=bot,
        rich_message=RICH_MESSAGE,
        telegram_id=1,
        training_id=10,
        outcome=BotTrainingSaveOutcome.CREATED,
    )

    api_client.update_group_bot_banned.assert_awaited_once_with(
        group_id=-1001,
        is_bot_banned=True,
    )
