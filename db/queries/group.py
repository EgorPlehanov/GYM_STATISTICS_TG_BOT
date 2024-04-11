from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert

from ..models import Group, GroupUser, User



async def is_group_in_database(session: AsyncSession, user_id: int):
    """
    Проверяет существует ли группа в базе данных
    """
    group = await session.execute(select(Group.id).filter_by(id = user_id))
    return group.first() is not None



async def create_group(
    session: AsyncSession,
    id: int,
    name: str,
    type: str

) -> None:
    """
    Добавляет группу в базу данных
    """
    session.add(Group(
        id = id,
        name = name,
        type = type.upper(),
    ))
    await session.commit()



async def update_group_is_bot_banned(
    session: AsyncSession,
    group_id: int,
    is_bot_banned: bool,
) -> None:
    """
    Обновляет статус блокировки бота в группе
    """
    await session.execute(
        update(Group)
        .values(
            is_bot_banned = is_bot_banned,
            is_bot_admin=False if is_bot_banned else Group.is_bot_admin
        )
        .filter_by(id = group_id)
    )
    await session.commit()



async def create_group_if_not_exists(
    session: AsyncSession,
    id: int,
    group_type: str,
    name: str,
) -> bool:
    """
    Создает группу в базе данных, если ее еще нет.
    """
    insert_stmt = insert(Group).values(id=id, name=name, type=group_type)
    insert_stmt = insert_stmt.on_conflict_do_nothing(index_elements=['id'])
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
    """
    Обновляет статус администратора в группе
    """
    await session.execute(
        update(Group)
        .values(is_bot_admin = is_bot_admin)
        .filter_by(id = group_id)
    )
    await session.commit()



async def update_group_to_supergroup(
    session: AsyncSession,
    group_id: int,
    supergroup_id: int
) -> None:
    """
    Обновляет у пользователей группу ссылку на супергруппу
    Группу удаляет из базы данных
    """
    await session.execute(
        update(GroupUser)
        .values(group_id = supergroup_id)
        .filter_by(group_id = group_id)
    )
    await session.execute(
        delete(Group)
        .filter_by(id = group_id)
    )
    await session.commit()