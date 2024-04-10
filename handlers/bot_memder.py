from aiogram import F, Router
from aiogram.filters import (
    ChatMemberUpdatedFilter,
    KICKED, MEMBER,
    JOIN_TRANSITION, LEAVE_TRANSITION, PROMOTED_TRANSITION
) 
from aiogram.types import ChatMemberUpdated

from sqlalchemy.ext.asyncio import AsyncSession

from config_reader import config
from middlewares import DBSessionMiddleware
from db.database import async_session_factory
from db.queries import (
    update_user_private_chat_banned,
    create_group_if_not_exists,
    update_group_is_bot_banned
)



router = Router()
router.my_chat_member.middleware(DBSessionMiddleware(async_session_factory))



@router.my_chat_member(
    F.chat.type == "private",
    ChatMemberUpdatedFilter(member_status_changed=KICKED)
)
async def user_blocked_bot(event: ChatMemberUpdated, session: AsyncSession):
    """
    Обновляет статус пользователя в БД при блокировке бота в личном чате
    """
    await update_user_private_chat_banned(
        session=session,
        user_id=event.from_user.id,
        is_private_chat_banned=True
    )



@router.my_chat_member(
    F.chat.type == "private",
    ChatMemberUpdatedFilter(member_status_changed=MEMBER)
)
async def user_unblocked_bot(event: ChatMemberUpdated, session: AsyncSession):
    """
    Обновляет статус пользователя в БД при разблокировке бота в личном чате
    """
    await update_user_private_chat_banned(
        session=session,
        user_id=event.from_user.id,
        is_private_chat_banned=False
    )
    await event.answer(f"{event.from_user.full_name}, с возвращением!\nДавай продолжим /training!")



@router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION)
)
async def bot_joined_to_group(event: ChatMemberUpdated, session: AsyncSession):
    """
    Бот добавлен в группу
    """
    is_created = await create_group_if_not_exists(
        session=session,
        id=event.chat.id,
        group_type=event.chat.type,
        name=event.chat.title,
    )
    hello_text = (
        f"Всем привет, я помогу вам отслеживать ваши тренировки!"
        if is_created
        else f"Я вернулся, можем продолжить тренировки вместе!"
    )
    await event.answer(
        f"{hello_text}\nЧтобы узнать больше, переходите в @{config.TG_BOT_USERNAME}"
    )



@router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION)
)
async def bot_joined_to_group(event: ChatMemberUpdated, session: AsyncSession):
    """
    Бот вышел в группу
    """
    await update_group_is_bot_banned(
        session=session,
        group_id=event.chat.id,
        is_bot_banned=True,
    )
    print("Выгнать меня из группы - это крокодилий поступок")



@router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ChatMemberUpdatedFilter(member_status_changed=PROMOTED_TRANSITION)
)
async def bot_joined_to_group(event: ChatMemberUpdated, session: AsyncSession):
    """
    Бот добавлен в группу
    """
    await event.answer(f"{event.from_user.full_name} назначил меня АДМИНОМ!\n Теперь сосать мне будете)")