from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import User



async def is_user_in_database(session: AsyncSession, user_id: int):
    """
    Проверяет существует ли пользователь в базе данных
    """
    user = await session.execute(select(User.id).filter_by(id = user_id))
    return user.first() is not None



async def create_user(session: AsyncSession, user: User):
    """
    Добавляет пользователя в базу данных
    """
    session.add(user)
    await session.commit()