from aiogram import F, Router
from aiogram.types import ChatMemberUpdated
from aiogram.filters import (
    ChatMemberUpdatedFilter,
    KICKED, MEMBER, LEFT, RESTRICTED,
    ADMINISTRATOR, CREATOR,
    IS_MEMBER, IS_NOT_MEMBER
) 

from sqlalchemy.ext.asyncio import AsyncSession

from middlewares import DBSessionMiddleware
from db.database import async_session_factory
from db.queries import (
    update_group_user_is_admin,
    delete_group_user,
)



router = Router()
router.chat_member.filter(F.chat.type.in_({"group", "supergroup"}))
router.chat_member.middleware(DBSessionMiddleware(async_session_factory))



@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated, session: AsyncSession):
    """
    Пользователь покинул чат
    """
    print(event.new_chat_member.user.first_name, event.new_chat_member.user.is_bot)
    if event.new_chat_member.user.is_bot:
        return
    await event.answer(
        text=f"Ура у нас пополнение, приветствуем {event.new_chat_member.user.full_name}!",
    )



@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_user_leave(event: ChatMemberUpdated, session: AsyncSession):
    """
    Пользователь покинул чат
    """
    if event.old_chat_member.user.is_bot:
        return
    await delete_group_user(
        session=session,
        group_id=event.chat.id,
        user_id=event.old_chat_member.user.id
    )
    await event.answer(
        text=f"Мб еще вернется(",
    )



@router.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=
        (KICKED | LEFT | RESTRICTED | MEMBER)
        >>
        (ADMINISTRATOR | CREATOR)
    )
)
async def admin_promoted(event: ChatMemberUpdated, session: AsyncSession):
    """
    Ползователь повышен до админа
    """
    await update_group_user_is_admin(
        session=session,
        group_id=event.chat.id,
        user_id=event.new_chat_member.user.id,
        is_admin=True
    )



@router.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=
        (ADMINISTRATOR | CREATOR)
        >>
        (KICKED | LEFT | RESTRICTED | MEMBER)
    )
)
async def admin_demoted(event: ChatMemberUpdated, session: AsyncSession):
    """
    Ползователь понижен до обычного юзера
    """
    await update_group_user_is_admin(
        session=session,
        group_id=event.chat.id,
        user_id=event.new_chat_member.user.id,
        is_admin=False
    )
