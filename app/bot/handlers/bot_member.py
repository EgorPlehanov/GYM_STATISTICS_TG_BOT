from asyncio import sleep

from aiogram import F, Router, html
from aiogram.filters import (
    JOIN_TRANSITION,
    KICKED,
    LEAVE_TRANSITION,
    MEMBER,
    PROMOTED_TRANSITION,
    ChatMemberUpdatedFilter,
)
from aiogram.types import ChatMemberUpdated, Message

from app.bot.client import BotApiClient
from app.bot.utils.migration_cache import cache
from app.core.config import config

router = Router()



@router.my_chat_member(
    F.chat.type == "private",
    ChatMemberUpdatedFilter(member_status_changed=KICKED)
)
async def user_blocked_bot(event: ChatMemberUpdated):
    """
    Обновляет статус пользователя в БД при блокировке бота в личном чате
    """
    async with BotApiClient() as api_client:
        await api_client.update_user_private_chat_banned(
            telegram_id=event.from_user.id,
            is_private_chat_banned=True,
        )



@router.my_chat_member(
    F.chat.type == "private",
    ChatMemberUpdatedFilter(member_status_changed=MEMBER)
)
async def user_unblocked_bot(event: ChatMemberUpdated):
    """
    Обновляет статус пользователя в БД при разблокировке бота в личном чате
    """
    async with BotApiClient() as api_client:
        await api_client.update_user_private_chat_banned(
            telegram_id=event.from_user.id,
            is_private_chat_banned=False,
        )
    await event.answer(f"{event.from_user.full_name}, с возвращением!\nДавай продолжим /training!")



@router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION)
)
async def bot_joined_to_group(event: ChatMemberUpdated):
    """
    Бот добавлен в группу
    """
    await sleep(1.0)
    # Если недавно группа была переведена в супергруппу
    if event.chat.id in cache.keys():
        return
    
    async with BotApiClient() as api_client:
        is_created = await api_client.ensure_group(
            group_id=event.chat.id,
            group_type=event.chat.type,
            group_name=event.chat.title,
        )
    hello_text = (
        "Всем привет, я помогу вам отслеживать ваши тренировки!"
        if is_created
        else "Я вернулась, можем продолжить тренировки вместе!"
    )
    await event.answer(
        text = (
            f"{hello_text}\n\nДля корректной работы "
            f"{html.bold('ОБЯЗАТЕЛЬНО СДЕЛАЙТЕ МЕНЯ АДМИНОМ.')}\n\n"
            f"Узнать больше /help@{config.TG_BOT_USERNAME}")
    )



@router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION)
)
async def bot_left_group(event: ChatMemberUpdated):
    """
    Бота удалили из группы
    """
    async with BotApiClient() as api_client:
        await api_client.update_group_bot_banned(
            group_id=event.chat.id,
            is_bot_banned=True,
        )



@router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ChatMemberUpdatedFilter(member_status_changed=PROMOTED_TRANSITION)
)
async def bot_promoted_to_group_admin(event: ChatMemberUpdated):
    """
    Бот добавлен в группу как админ
    """
    async with BotApiClient() as api_client:
        await api_client.update_group_bot_admin(
            group_id=event.chat.id,
            is_bot_admin=True,
        )
    await event.answer(
        f"{event.from_user.full_name} назначил меня АДМИНОМ!\n"
        " Теперь я смогу устанавливать ваш ранг в должности админа"
    )



@router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ChatMemberUpdatedFilter(member_status_changed=~PROMOTED_TRANSITION)
)
async def bot_demoted_from_group_admin(event: ChatMemberUpdated):
    """
    Бот добавлен в группу как пользователь
    """
    async with BotApiClient() as api_client:
        await api_client.update_group_bot_admin(
            group_id=event.chat.id,
            is_bot_admin=False,
        )
    await event.answer(
        f"{event.from_user.full_name} меня разжаловал!\n"
        " Теперь я не смогу устанавливать ранг в должности админа"
    )



@router.message(F.migrate_from_chat_id)
async def migrate_group_to_supergroup(message: Message):
    """
    Миграция группы в супергруппу
    """
    cache[message.chat.id] = True
    async with BotApiClient() as api_client:
        await api_client.migrate_group_to_supergroup(
            group_id=message.migrate_from_chat_id,
            supergroup_id=message.chat.id,
            supergroup_name=message.chat.title,
            supergroup_type=message.chat.type,
        )

