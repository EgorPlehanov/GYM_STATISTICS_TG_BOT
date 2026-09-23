"""Сигнал готовности Telegram-бота для Docker healthcheck."""

from pathlib import Path

from aiogram import Bot

BOT_READINESS_FILE = Path("/tmp/gym-statistics-bot.ready")


def clear_bot_readiness() -> None:
    """Удаляет readiness-маркер перед каждой новой попыткой запуска бота."""
    BOT_READINESS_FILE.unlink(missing_ok=True)


async def notify_admin_and_mark_bot_ready(
    bot: Bot,
    *,
    admin_chat_id: int,
    app_env: str,
) -> None:
    """Уведомляет администратора и отмечает бота готовым после ответа Telegram.

    Args:
        bot: Telegram-клиент, созданный для текущего процесса бота.
        admin_chat_id: chat id главного администратора для стартового сообщения.
        app_env: имя текущего окружения приложения.

    Raises:
        TelegramAPIError: если Telegram не подтвердил доставку сообщения.
            Readiness-файл при этом не создается, а процесс должен завершиться.
    """
    await bot.send_message(
        chat_id=admin_chat_id,
        text=(
            "✅ Бот готов к работе\n"
            f"Окружение: {app_env}\n"
            "Режим: polling"
        ),
    )
    _write_readiness_file()


def _write_readiness_file() -> None:
    """Атомарно создает readiness-файл после успешного старта."""
    temporary_file = BOT_READINESS_FILE.with_suffix(".tmp")
    temporary_file.write_text("ready\n", encoding="ascii")
    temporary_file.replace(BOT_READINESS_FILE)
