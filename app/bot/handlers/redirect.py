from aiogram import F, Router, html
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from typing import List
from asyncio import sleep 

from app.core.config import config
from app.bot.middlewares import DBSessionMiddleware
from app.db.session import async_session_factory
from app.db.repositories import (
    is_user_in_database,
    update_redirect_to_group,
    create_group_user,
    get_group_user_by_user_id_and_group_id,
    get_all_user_redirect_groups
)
from app.bot.keyboards.keyboards_types import PaginationAction
from app.bot.keyboards.redirect_kb import (
    get_ikb_redirect_groups,
    RedirectGroupPagination
)
from app.bot.handlers.redirect_units import RedirectStates, RedirectGroup



router = Router()
router.message.middleware(DBSessionMiddleware(async_session_factory))
router.callback_query.middleware(DBSessionMiddleware(async_session_factory))



@router.message(
    StateFilter(None),
    Command("redirect"),
    F.chat.type.in_({"group", "supergroup"})
)
async def cmd_group_redirect(message: Message, session: AsyncSession) -> None:
    """
    Команда /redirect для групп устанавливает пересылку сообщениий о тренировке
    в текущую группу для отправителя сообщения
    """
    if not await is_user_in_database(
        session = session,
        user_id = message.from_user.id,
    ):
        await message.answer(f"Сначала нужно запустить бота @{config.TG_BOT_USERNAME}")
        return

    group_user = await get_group_user_by_user_id_and_group_id(
        session = session,
        user_id = message.from_user.id,
        group_id = message.chat.id
    )
    if group_user is None:
        is_redirect = True
        is_user_admin = message.from_user.id in [
            a.user.id for a in await message.bot.get_chat_administrators(message.chat.id)
        ]
        await create_group_user(
            session = session,
            user_id = message.from_user.id,
            group_id = message.chat.id,
            is_user_admin = is_user_admin,
            is_redirect_to_group = True,
        )
    else:
        is_redirect = not group_user.is_redirect_to_group
        await update_redirect_to_group(
            session = session,
            group_id = message.chat.id,
            user_id = message.from_user.id,
            is_redirect_to_group = not group_user.is_redirect_to_group
        )

    await message.answer(
        text = (
            f"📤{'✅' if is_redirect else '❌'}"
            f" @{message.from_user.username}, я "
            f"{html.bold('ВКЛЮЧИЛ' if is_redirect else 'ОТКЛЮЧИЛ')}"
            " редирект в эту группу! Чтобы "
            f"{html.bold('отключить' if is_redirect else 'включить')}"
            " отправь повторно /redirect."
        ) + (
            f"\n\nСоздавай тренировки через личку бота @{config.TG_BOT_USERNAME}" + \
            f" командой /training и результаты будут пересылаться в эту группу"
            if group_user is None else ""
        )
    )



@router.message(
    StateFilter(None),
    Command("redirect"),
    F.chat.type == "private"
)
async def cmd_private_redirect(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """
    Команда /redirect для лс с ботом
    """
    await message.delete()

    await state.set_state(RedirectStates.edit_redirect_group)

    redirect_groups: List[RedirectGroup] = await get_all_user_redirect_groups(
        session = session,
        user_id = message.from_user.id
    )

    await state.update_data(redirect_groups=redirect_groups)

    await message.answer(
        text = (
            "📤 Спиок чатов в которых настроен редирект результатов тренировок:\n"
            f"{html.italic('(✅ - вкл | ⛔ - выкл)')}"
        ),
        reply_markup = get_ikb_redirect_groups(
            redirect_groups = redirect_groups
        )
    )



@router.callback_query(
    RedirectGroupPagination.filter(F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])),
    RedirectStates.edit_redirect_group,
)
async def redirect_group_pagination(
    callback: CallbackQuery,
    callback_data: RedirectGroupPagination,
    state: FSMContext
):
    """
    Пагинация редиректа в группы
    """
    page = int(callback_data.page)

    user_data = await state.get_data()
    redirect_groups: List[RedirectGroup] = user_data.get("redirect_groups")

    if callback_data.action == PaginationAction.PREV:
        page = page - 1 if page > 0 else 0
    elif callback_data.action == PaginationAction.NEXT:
        page = page + 1 if page < len(redirect_groups) - 1 else page

    await callback.message.edit_reply_markup(
        reply_markup = get_ikb_redirect_groups(
            redirect_groups = redirect_groups,
            page = page
        )
    )
    


@router.callback_query(
    RedirectGroupPagination.filter(F.action == PaginationAction.SET),
    RedirectStates.edit_redirect_group
)
async def edit_redirect_group(
    callback: CallbackQuery,
    callback_data: RedirectGroupPagination,
    state: FSMContext,
    session: AsyncSession
) -> None:
    """
    Инлайн кнопка "Меню настройки редиректа в группы" возврат в меню
    """
    user_data = await state.get_data()
    redirect_groups: List[RedirectGroup] = user_data.get("redirect_groups")

    edited_r_gr = next((r_gr for r_gr in redirect_groups if r_gr.group_id == callback_data.redirect_group_id), None)
    edited_r_gr.is_redirect_to_group = not edited_r_gr.is_redirect_to_group

    await update_redirect_to_group(
        session = session,
        group_id = edited_r_gr.group_id,
        user_id = callback.from_user.id,
        is_redirect_to_group = edited_r_gr.is_redirect_to_group
    )

    await callback.message.edit_reply_markup(
        reply_markup = get_ikb_redirect_groups(
            redirect_groups = redirect_groups,
            page = callback_data.page
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

