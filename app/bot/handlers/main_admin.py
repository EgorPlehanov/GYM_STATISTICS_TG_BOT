from aiogram import F, Router, html
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import InputRichMessage, Message

from app.bot.client import BotApiClient
from app.bot.filters.main_admin import MainAdminFilter
from app.bot.formatters.training_previews import build_training_previews
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
            "/training_designs - посмотреть макеты сообщений тренировки в личке\n"
        )
    )


@router.message(Command("training_designs"), F.chat.type == "private")
async def training_designs(message: Message) -> None:
    """Показывает админу все ParseMode и структурные Rich Messages."""
    for preview in build_training_previews():
        if preview.rich_format is None:
            await message.answer(text=preview.text, parse_mode=preview.parse_mode)
            continue

        try:
            await message.bot.send_rich_message(
                chat_id=message.chat.id,
                rich_message=InputRichMessage(**{preview.rich_format.value: preview.text}),
            )
        except TelegramAPIError as error:
            await message.answer(
                text=(
                    f"⚠️ {html.quote(preview.title)}: "
                    f"Rich Message не отправлено ({html.quote(error.message)})."
                ),
                parse_mode=ParseMode.HTML,
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
