from aiogram import F, Router, html
from aiogram.filters import (
    ChatMemberUpdatedFilter,
    KICKED, MEMBER,
    JOIN_TRANSITION, LEAVE_TRANSITION, PROMOTED_TRANSITION,
) 
from aiogram.types import ChatMemberUpdated, Message

from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import sleep 

from config_reader import config
from middlewares import DBSessionMiddleware
from db.database import async_session_factory
from db.queries import (
    update_user_private_chat_banned,
    create_group_if_not_exists,
    update_group_is_bot_banned,
    update_group_is_bot_admin,
    update_group_to_supergroup,
)
from utils.migration_cache import cache
# from utils.get_chat_members import get_chat_members



router = Router()
router.my_chat_member.middleware(DBSessionMiddleware(async_session_factory))
router.message.middleware(DBSessionMiddleware(async_session_factory))



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
    await sleep(1.0)
    # Если недавно группа была переведена в супергруппу
    if event.chat.id in cache.keys():
        return
    
    is_created = await create_group_if_not_exists(
        session=session,
        id=event.chat.id,
        group_type=event.chat.type,
        name=event.chat.title,
    )
    hello_text = (
        f"Всем привет, я помогу вам отслеживать ваши тренировки!"
        if is_created
        else f"Я вернулась, можем продолжить тренировки вместе!"
    )
    await event.answer(
        text = (
            f"{hello_text}\n\nДля корректной работы "
            f"{html.bold('ОБЯЗАТЕЛЬНО СДЕЛАЙТЕ БОТА АДМИНОМ.')}\n\n"
            f"Узнать больше /help@{config.TG_BOT_USERNAME}")
    )



@router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION)
)
async def bot_joined_to_group(event: ChatMemberUpdated, session: AsyncSession):
    """
    Бота удалили из группы
    """
    await update_group_is_bot_banned(
        session=session,
        group_id=event.chat.id,
        is_bot_banned=True,
    )



@router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ChatMemberUpdatedFilter(member_status_changed=PROMOTED_TRANSITION)
)
async def bot_joined_to_group(event: ChatMemberUpdated, session: AsyncSession):
    """
    Бот добавлен в группу как админ
    """
    await update_group_is_bot_admin(
        session=session,
        group_id=event.chat.id,
        is_bot_admin=True,
    )
    await event.answer(f"{event.from_user.full_name} назначил меня АДМИНОМ!\n Теперь я смогу устанавливать ваш ранг в должности админа")



@router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ChatMemberUpdatedFilter(member_status_changed=~PROMOTED_TRANSITION)
)
async def bot_joined_to_group(event: ChatMemberUpdated, session: AsyncSession):
    """
    Бот добавлен в группу как пользователь
    """
    await update_group_is_bot_admin(
        session=session,
        group_id=event.chat.id,
        is_bot_admin=False,
    )
    await event.answer(f"{event.from_user.full_name} меня разжаловал!\n Теперь я не смогу устанавливать ранг в должности админа")



@router.message(F.migrate_from_chat_id)
async def migrate_group_to_supergroup(message: Message, session: AsyncSession):
    """
    Миграция группы в супергруппу
    """
    cache[message.chat.id] = True
    await update_group_to_supergroup(
        session=session,
        group_id=message.migrate_from_chat_id,
        supergroup_id=message.chat.id
    )