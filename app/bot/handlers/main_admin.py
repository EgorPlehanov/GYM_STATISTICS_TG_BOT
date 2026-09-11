from aiogram import Router, html
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.client import BotApiClient
from app.bot.filters.main_admin import MainAdminFilter
from app.bot.middlewares import ChatActionMiddleware

router = Router()
router.message.filter(MainAdminFilter())
router.message.middleware(ChatActionMiddleware())


@router.message(Command("admincmd"))
async def admin_cmd(message: Message):
    await message.answer(
        text=(
            f"{html.bold('Минимальная admin-панель')}\n\n"
            "/admin_status - проверить доступность backend API\n"
        )
    )


@router.message(Command("admin_status"))
async def admin_status(message: Message):
    """Показывает безопасный статус backend API для администратора."""
    try:
        async with BotApiClient() as api_client:
            status = await api_client.get_admin_status(message.from_user.id)
    except Exception as e:
        await message.answer(text=f"❌ Backend API недоступен: {str(e)}")
        return

    roles = ", ".join(status.roles) if status.roles else "нет ролей"
    await message.answer(
        text=(
            f"✅ Backend API: {html.bold(status.api_status)}\n"
            f"Окружение: {html.code(status.app_env)}\n"
            f"Доступ: {html.bold('разрешен' if status.has_access else 'запрещен')}\n"
            f"Роли: {html.code(roles)}"
        )
    )
