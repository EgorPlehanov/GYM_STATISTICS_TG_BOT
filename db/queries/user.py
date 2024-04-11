from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from ..models import User



async def is_user_in_database(session: AsyncSession, user_id: int):
    """
    Проверяет существует ли пользователь в базе данных
    """
    user = await session.execute(select(User.id).filter_by(id = user_id))
    return user.first() is not None



async def create_user(
    session: AsyncSession,
    user_id: User,
    name: str,
    language_code: str,
):
    """
    Добавляет пользователя в базу данных
    """
    session.add(User(
        id=user_id,
        name=name,
        language_code=language_code,
    ))
    await session.commit()



async def update_user_private_chat_banned(
    session: AsyncSession,
    user_id: int,
    is_private_chat_banned: bool
) -> None:
    """
    Обновляет статус блокировки приватного чата
    """
    await session.execute(
        update(User)
        .values(is_bot_banned = is_private_chat_banned)
        .filter_by(id = user_id)
    )
    await session.commit()



async def create_user_if_not_exists(
    session: AsyncSession,
    user_id: User,
    name: str,
    language_code: str,
) -> bool:
    """
    Создает группу в базе данных, если ее еще нет.
    """
    insert_stmt = (
        insert(User)
        .values(
            id=user_id,
            name=name,
            language_code=language_code,
        )
    )
    insert_stmt = insert_stmt.on_conflict_do_nothing(index_elements=['id'])
    result = await session.execute(insert_stmt)
    await session.commit()

    is_created = bool(result.rowcount)
    return is_created