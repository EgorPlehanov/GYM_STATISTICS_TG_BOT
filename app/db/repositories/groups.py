"""Репозиторий Telegram-групп."""

from collections import namedtuple

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Group, GroupTrainingResultMessage, GroupUser
from app.db.repositories.users import get_internal_user_id_by_telegram_id


class GroupRepository:
    """Доступ к данным Telegram-групп."""


RedirectGroup = namedtuple(
    "RedirectGroup",
    ["id", "group_id", "group_name", "is_redirect_to_group"],
)


async def is_group_in_database(session: AsyncSession, user_id: int) -> bool:
    """Проверяет, существует ли группа в базе данных."""
    group = await session.execute(select(Group.id).filter_by(id=user_id))
    return group.first() is not None


async def create_group(
    session: AsyncSession,
    id: int,
    name: str,
    type: str,
) -> None:
    """Добавляет Telegram-группу в базу данных."""
    session.add(
        Group(
            id=id,
            name=name,
            type=type.upper(),
        )
    )
    await session.commit()


async def update_group_is_bot_banned(
    session: AsyncSession,
    group_id: int,
    is_bot_banned: bool,
) -> None:
    """Обновляет статус блокировки бота в группе."""
    await session.execute(
        update(Group)
        .values(
            is_bot_banned=is_bot_banned,
            is_bot_admin=False if is_bot_banned else Group.is_bot_admin,
        )
        .filter_by(id=group_id)
    )
    await session.commit()


async def create_group_if_not_exists(
    session: AsyncSession,
    id: int,
    group_type: str,
    name: str,
) -> bool:
    """Создает Telegram-группу, если ее еще нет."""
    insert_stmt = insert(Group).values(id=id, name=name, type=group_type)
    insert_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["id"])
    result = await session.execute(insert_stmt)
    await session.commit()

    is_created = bool(result.rowcount)
    if not is_created:
        await update_group_is_bot_banned(
            session=session,
            group_id=id,
            is_bot_banned=False,
        )
    return is_created


async def update_group_is_bot_admin(
    session: AsyncSession,
    group_id: int,
    is_bot_admin: bool,
) -> None:
    """Обновляет статус администратора бота в группе."""
    await session.execute(
        update(Group)
        .values(is_bot_admin=is_bot_admin)
        .filter_by(id=group_id)
    )
    await session.commit()


async def update_group_to_supergroup(
    session: AsyncSession,
    group_id: int,
    supergroup_id: int,
    supergroup_name: str,
    supergroup_type: str,
) -> None:
    """Переносит связи старой группы на супергруппу и удаляет старую группу."""
    insert_stmt = insert(Group).values(
        id=supergroup_id,
        name=supergroup_name,
        type=supergroup_type.upper(),
        is_bot_banned=False,
    )
    insert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "name": supergroup_name,
            "type": supergroup_type.upper(),
            "is_bot_banned": False,
        },
    )
    await session.execute(insert_stmt)
    await session.execute(
        update(GroupUser)
        .values(group_id=supergroup_id)
        .filter_by(group_id=group_id)
    )
    await session.execute(
        update(GroupTrainingResultMessage)
        .values(group_id=supergroup_id)
        .filter_by(group_id=group_id)
    )
    await session.execute(delete(Group).filter_by(id=group_id))
    await session.commit()


async def check_user_in_group(
    session: AsyncSession,
    user_id: int,
    group_id: int,
) -> bool:
    """Проверяет, состоит ли пользователь с Telegram id в группе."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return False

    result = await session.execute(
        select(GroupUser).filter_by(user_id=internal_user_id, group_id=group_id)
    )
    return bool(result.scalar())


async def get_group_user_by_user_id_and_group_id(
    session: AsyncSession,
    user_id: int,
    group_id: int,
) -> GroupUser | None:
    """Возвращает связь пользователя с Telegram id и группы."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return None

    result = await session.execute(
        select(GroupUser).filter_by(user_id=internal_user_id, group_id=group_id)
    )
    return result.scalar()


async def create_group_user(
    session: AsyncSession,
    user_id: int,
    group_id: int,
    is_user_admin: bool,
    is_redirect_to_group: bool = False,
) -> bool:
    """Добавляет пользователя с Telegram id в группу."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return False

    insert_stmt = insert(GroupUser).values(
        user_id=internal_user_id,
        group_id=group_id,
        is_user_admin=is_user_admin,
        is_redirect_to_group=is_redirect_to_group,
    )
    insert_stmt = insert_stmt.on_conflict_do_nothing(
        index_elements=["group_id", "user_id"],
    )
    result = await session.execute(insert_stmt)
    await session.commit()
    return bool(result.rowcount)


async def update_redirect_to_group(
    session: AsyncSession,
    user_id: int,
    group_id: int,
    is_redirect_to_group: bool,
) -> None:
    """Обновляет статус перенаправления результатов пользователя в группу."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return

    await session.execute(
        update(GroupUser)
        .values(is_redirect_to_group=is_redirect_to_group)
        .filter_by(user_id=internal_user_id, group_id=group_id)
    )
    await session.commit()


async def get_all_user_redirect_groups(
    session: AsyncSession,
    user_id: int,
) -> list[RedirectGroup]:
    """Возвращает группы пользователя с Telegram id, доступные для настройки редиректа."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return []

    result = await session.execute(
        select(
            GroupUser.id,
            GroupUser.group_id,
            Group.name,
            GroupUser.is_redirect_to_group,
        )
        .join(Group, GroupUser.group_id == Group.id)
        .where(
            GroupUser.user_id == internal_user_id,
            Group.is_bot_banned.is_(False),
        )
    )
    return [
        RedirectGroup(
            id=row[0],
            group_id=row[1],
            group_name=row[2],
            is_redirect_to_group=row[3],
        )
        for row in result.all()
    ]


async def get_user_group_to_redirect(
    session: AsyncSession,
    user_id: int,
) -> list[int]:
    """Возвращает id групп, куда включен редирект результатов пользователя."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return []

    result = await session.execute(
        select(GroupUser.group_id)
        .join(Group, GroupUser.group_id == Group.id)
        .where(
            GroupUser.user_id == internal_user_id,
            GroupUser.is_redirect_to_group.is_(True),
            Group.is_bot_banned.is_(False),
        )
    )
    return [row[0] for row in result.all()]


async def update_group_user_is_admin(
    session: AsyncSession,
    group_id: int,
    user_id: int,
    is_admin: bool,
) -> None:
    """Обновляет статус администратора пользователя с Telegram id в группе."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return

    await session.execute(
        update(GroupUser)
        .values(is_user_admin=is_admin)
        .filter_by(
            group_id=group_id,
            user_id=internal_user_id,
        )
    )
    await session.commit()


async def delete_group_user(
    session: AsyncSession,
    group_id: int,
    user_id: int,
) -> None:
    """Удаляет пользователя с Telegram id из группы."""
    internal_user_id = await get_internal_user_id_by_telegram_id(session, user_id)
    if internal_user_id is None:
        return

    await session.execute(
        delete(GroupUser).filter_by(group_id=group_id, user_id=internal_user_id)
    )
    await session.commit()


async def upsert_group_training_result_message(
    session: AsyncSession,
    group_id: int,
    training_id: int,
    message_id: int,
) -> None:
    """Создает или обновляет связь результата тренировки с Telegram-сообщением.

    Пара `group_id` и `training_id` однозначно определяет сообщение результата.
    PostgreSQL выполняет вставку или обновление одной атомарной командой.
    """
    statement = insert(GroupTrainingResultMessage).values(
        group_id=group_id,
        training_id=training_id,
        message_id=message_id,
    )
    await session.execute(
        statement.on_conflict_do_update(
            index_elements=[
                GroupTrainingResultMessage.group_id,
                GroupTrainingResultMessage.training_id,
            ],
            set_={
                "message_id": statement.excluded.message_id,
                "updated_at": func.now(),
            },
        )
    )
    await session.commit()


async def get_group_training_result_messages_id(
    session: AsyncSession,
    group_id: int,
    training_id: int,
) -> int | None:
    """Возвращает Telegram message id результата тренировки в группе."""
    result = await session.execute(
        select(GroupTrainingResultMessage.message_id).where(
            GroupTrainingResultMessage.group_id == group_id,
            GroupTrainingResultMessage.training_id == training_id,
        )
    )
    first_result = result.first()
    if first_result is not None:
        return first_result[0]
    return None
