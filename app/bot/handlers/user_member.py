from aiogram import F, Router
from aiogram.filters import (
    ADMINISTRATOR,
    CREATOR,
    IS_MEMBER,
    IS_NOT_MEMBER,
    KICKED,
    LEFT,
    MEMBER,
    RESTRICTED,
    ChatMemberUpdatedFilter,
)
from aiogram.types import ChatMemberUpdated

from app.bot.client import BotApiClient

router = Router()
router.chat_member.filter(F.chat.type.in_({"group", "supergroup"}))



@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    """
    Пользователь присоединился к чату
    """
    if event.new_chat_member.user.is_bot:
        return
    await event.answer(
        text=f"Ура у нас пополнение, приветствуем {event.new_chat_member.user.full_name}!",
    )



@router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_user_leave(event: ChatMemberUpdated):
    """
    Пользователь покинул чат
    """
    if event.old_chat_member.user.is_bot:
        return
    async with BotApiClient() as api_client:
        await api_client.delete_group_user(
            group_id=event.chat.id,
            telegram_id=event.old_chat_member.user.id,
        )
    await event.answer(
        text="Мб еще вернется(",
    )



@router.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=
        (KICKED | LEFT | RESTRICTED | MEMBER)
        >>
        (ADMINISTRATOR | CREATOR)
    )
)
async def admin_promoted(event: ChatMemberUpdated):
    """
    Пользователь повышен до админа
    """
    async with BotApiClient() as api_client:
        await api_client.update_group_user_admin(
            group_id=event.chat.id,
            telegram_id=event.new_chat_member.user.id,
            is_admin=True,
        )



@router.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=
        (ADMINISTRATOR | CREATOR)
        >>
        (KICKED | LEFT | RESTRICTED | MEMBER)
    )
)
async def admin_demoted(event: ChatMemberUpdated):
    """
    Пользователь понижен до обычного юзера
    """
    async with BotApiClient() as api_client:
        await api_client.update_group_user_admin(
            group_id=event.chat.id,
            telegram_id=event.new_chat_member.user.id,
            is_admin=False,
        )


