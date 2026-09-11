from aiogram import F, Router, html
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.api_client.schemas.groups import BotRedirectGroup
from app.bot.client import BotApiClient
from app.bot.handlers.redirect_units import RedirectStates
from app.bot.keyboards.keyboards_types import PaginationAction
from app.bot.keyboards.redirect_kb import RedirectGroupPagination, get_ikb_redirect_groups
from app.bot.utils.user_access import ensure_bot_user
from app.core.config import config

router = Router()


@router.message(StateFilter(None), Command("redirect"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_group_redirect(message: Message) -> None:
    """
    Команда /redirect для групп устанавливает пересылку сообщениий о тренировке
    в текущую группу для отправителя сообщения
    """
    await ensure_bot_user(message.from_user)

    is_user_admin = message.from_user.id in [
        a.user.id for a in await message.bot.get_chat_administrators(message.chat.id)
    ]
    async with BotApiClient() as api_client:
        result = await api_client.toggle_current_group_redirect(
            telegram_id=message.from_user.id,
            group_id=message.chat.id,
            group_name=message.chat.title,
            group_type=message.chat.type,
            is_user_admin=is_user_admin,
        )

    await message.answer(
        text=(
            f"📤{'✅' if result.is_redirect_to_group else '❌'}"
            f" @{message.from_user.username}, я "
            f"{html.bold('ВКЛЮЧИЛ' if result.is_redirect_to_group else 'ОТКЛЮЧИЛ')}"
            " редирект в эту группу! Чтобы "
            f"{html.bold('отключить' if result.is_redirect_to_group else 'включить')}"
            " отправь повторно /redirect."
        )
        + (
            f"\n\nСоздавай тренировки через личку бота @{config.TG_BOT_USERNAME}"
            + " командой /training и результаты будут пересылаться в эту группу"
            if result.created
            else ""
        )
    )


@router.message(StateFilter(None), Command("redirect"), F.chat.type == "private")
async def cmd_private_redirect(message: Message, state: FSMContext) -> None:
    """
    Команда /redirect для лс с ботом
    """
    await ensure_bot_user(message.from_user)

    await message.delete()

    await state.set_state(RedirectStates.edit_redirect_group)

    async with BotApiClient() as api_client:
        redirect_groups = await api_client.get_redirect_groups(message.from_user.id)

    await state.update_data(redirect_groups=redirect_groups)

    await message.answer(
        text=(
            "📤 Спиок чатов в которых настроен редирект результатов тренировок:\n"
            f"{html.italic('(✅ - вкл | ⛔ - выкл)')}"
        ),
        reply_markup=get_ikb_redirect_groups(redirect_groups=redirect_groups),
    )


@router.callback_query(
    RedirectGroupPagination.filter(F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])),
    RedirectStates.edit_redirect_group,
)
async def redirect_group_pagination(
    callback: CallbackQuery, callback_data: RedirectGroupPagination, state: FSMContext
):
    """
    Пагинация редиректа в группы
    """
    page = int(callback_data.page)

    user_data = await state.get_data()
    redirect_groups: list[BotRedirectGroup] = user_data.get("redirect_groups")

    if callback_data.action == PaginationAction.PREV:
        page = page - 1 if page > 0 else 0
    elif callback_data.action == PaginationAction.NEXT:
        page = page + 1 if page < len(redirect_groups) - 1 else page

    await callback.message.edit_reply_markup(
        reply_markup=get_ikb_redirect_groups(redirect_groups=redirect_groups, page=page)
    )


@router.callback_query(
    RedirectGroupPagination.filter(F.action == PaginationAction.SET),
    RedirectStates.edit_redirect_group,
)
async def edit_redirect_group(
    callback: CallbackQuery,
    callback_data: RedirectGroupPagination,
    state: FSMContext,
) -> None:
    """
    Инлайн кнопка "Меню настройки редиректа в группы" возврат в меню
    """
    user_data = await state.get_data()
    redirect_groups: list[BotRedirectGroup] = user_data.get("redirect_groups")

    edited_r_gr = next(
        (r_gr for r_gr in redirect_groups if r_gr.group_id == callback_data.redirect_group_id),
        None,
    )
    edited_r_gr.is_redirect_to_group = not edited_r_gr.is_redirect_to_group

    async with BotApiClient() as api_client:
        await api_client.update_redirect_group(
            telegram_id=callback.from_user.id,
            group_id=edited_r_gr.group_id,
            is_redirect_to_group=edited_r_gr.is_redirect_to_group,
        )

    await callback.message.edit_reply_markup(
        reply_markup=get_ikb_redirect_groups(
            redirect_groups=redirect_groups, page=callback_data.page
        )
    )


@router.callback_query(RedirectStates.edit_redirect_group, F.data == "redirect_quit")
async def redirect_quit(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Инлайн кнопка "Выход из настройки редиректа в группы" возврат в меню
    """
    await state.clear()
    await callback.message.delete()
    await callback.answer(text="✅ Настройки редиректа сохранены 💾")
