"""Репозиторий пользователей."""

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserRepository:
    """Доступ к данным пользователей."""


async def get_internal_user_id_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
) -> int | None:
    """Возвращает внутренний id пользователя по Telegram id.

    Вход:
        session: асинхронная SQLAlchemy-сессия.
        telegram_id: внешний Telegram user id.
    Выход:
        внутренний `User.id` или `None`, если пользователь не найден.
    """
    return await session.scalar(select(User.id).where(User.telegram_id == telegram_id))


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Возвращает пользователя по внутреннему id."""
    return await session.scalar(select(User).where(User.id == user_id))


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    """Возвращает пользователя по Telegram id."""
    return await session.scalar(select(User).where(User.telegram_id == telegram_id))


async def is_user_in_database(session: AsyncSession, user_id: int) -> bool:
    """Проверяет, существует ли пользователь с указанным Telegram id."""
    user = await session.execute(select(User.id).where(User.telegram_id == user_id))
    return user.first() is not None


async def create_user(
    session: AsyncSession,
    user_id: int,
    name: str,
    language_code: str | None,
) -> None:
    """Добавляет пользователя в базу данных.

    `user_id` здесь сохраняет старый контракт бота и означает Telegram user id.
    """
    session.add(
        User(
            telegram_id=user_id,
            name=name,
            language_code=language_code,
        )
    )
    await session.commit()


async def update_user_private_chat_banned(
    session: AsyncSession,
    user_id: int,
    is_private_chat_banned: bool,
) -> None:
    """Обновляет статус блокировки бота пользователем в личном чате."""
    await session.execute(
        update(User)
        .values(is_bot_banned=is_private_chat_banned)
        .where(User.telegram_id == user_id)
    )
    await session.commit()


async def create_user_if_not_exists(
    session: AsyncSession,
    user_id: int,
    name: str,
    language_code: str | None,
) -> bool:
    """Создает пользователя, если его еще нет.

    `user_id` - Telegram user id. Внутренний `User.id` генерируется базой данных.
    """
    insert_stmt = insert(User).values(
        telegram_id=user_id,
        name=name,
        language_code=language_code,
    )
    insert_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["telegram_id"])
    result = await session.execute(insert_stmt)
    await session.commit()

    return bool(result.rowcount)


async def create_or_update_user_from_telegram(
    session: AsyncSession,
    telegram_id: int,
    name: str,
    language_code: str | None = None,
) -> User:
    """Создает или обновляет пользователя по данным Telegram.

    Вход:
        telegram_id: внешний Telegram user id.
        name: отображаемое имя из Telegram Login Widget или бота.
        language_code: языковой код, если Telegram передал его в текущем сценарии.

    Выход:
        актуальный объект пользователя после сохранения.
    """
    insert_stmt = insert(User).values(
        telegram_id=telegram_id,
        name=name,
        language_code=language_code,
    )
    update_values = {
        "name": name,
    }
    if language_code is not None:
        update_values["language_code"] = language_code

    await session.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=["telegram_id"],
            set_=update_values,
        )
    )
    await session.commit()

    user = await get_user_by_telegram_id(session, telegram_id)
    if user is None:
        raise ValueError("Не удалось получить пользователя после авторизации")
    return user
