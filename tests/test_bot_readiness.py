"""Тесты readiness-сигнала Telegram-бота."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.bot import readiness


async def test_successful_admin_notification_marks_bot_ready(monkeypatch, tmp_path) -> None:
    """Бот становится готовым только после успешной отправки админу."""
    readiness_file = tmp_path / "bot.ready"
    monkeypatch.setattr(readiness, "BOT_READINESS_FILE", readiness_file)
    bot = SimpleNamespace(send_message=AsyncMock())

    readiness.clear_bot_readiness()
    await readiness.notify_admin_and_mark_bot_ready(
        bot,
        admin_chat_id=123,
        app_env="test",
    )

    bot.send_message.assert_awaited_once_with(
        chat_id=123,
        text="✅ Бот готов к работе\nОкружение: test\nРежим: polling",
    )
    assert readiness_file.read_text(encoding="ascii") == "ready\n"


async def test_failed_admin_notification_does_not_mark_bot_ready(monkeypatch, tmp_path) -> None:
    """Ошибка Telegram не создает readiness-файл и остается видимой startup-коду."""
    readiness_file = tmp_path / "bot.ready"
    readiness_file.write_text("outdated\n", encoding="ascii")
    monkeypatch.setattr(readiness, "BOT_READINESS_FILE", readiness_file)
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=RuntimeError("Telegram down")))

    readiness.clear_bot_readiness()
    with pytest.raises(RuntimeError, match="Telegram down"):
        await readiness.notify_admin_and_mark_bot_ready(
            bot,
            admin_chat_id=123,
            app_env="test",
        )

    assert not readiness_file.exists()
