"""Репозиторий пользователей."""

from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Role, User, UserRole


class UserRepository:
    """Доступ к данным пользователей."""


async def get_internal_user_id_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
) -> int | None:
    """Возвращает внутренний id пользователя по Telegram id.

    Args:
        session: асинхронная SQLAlchemy-сессия.
        telegram_id: внешний Telegram user id.
    Returns:
        внутренний `User.id` или `None`, если пользователь не найден.
    """
    return await session.scalar(select(User.id).where(User.telegram_id == telegram_id))


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Возвращает пользователя по внутреннему id."""
    return await session.scalar(select(User).where(User.id == user_id))


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    """Возвращает пользователя по Telegram id."""
    return await session.scalar(select(User).where(User.telegram_id == telegram_id))


async def get_role_by_code(session: AsyncSession, code: str) -> Role | None:
    """Возвращает роль по стабильному коду."""
    return await session.scalar(select(Role).where(Role.code == code))


async def assign_role_to_user(
    session: AsyncSession,
    user_id: int,
    role_code: str,
    assigned_by_user_id: int | None = None,
) -> bool:
    """Назначает роль пользователю и возвращает признак создания назначения.

    Args:
        session: асинхронная SQLAlchemy-сессия.
        user_id: внутренний id пользователя.
        role_code: стабильный код роли.
        assigned_by_user_id: внутренний id пользователя, назначившего роль.

    Returns:
        `True`, если назначение роли создано в текущем запросе.
    """
    role = await get_role_by_code(session, role_code)
    if role is None:
        raise ValueError(
            f"Роль `{role_code}` не найдена. Проверьте миграции и seed-данные.",
        )

    insert_stmt = insert(UserRole).values(
        user_id=user_id,
        role_id=role.id,
        assigned_by_user_id=assigned_by_user_id,
    )
    insert_stmt = insert_stmt.on_conflict_do_nothing(
        index_elements=["user_id", "role_id"],
    )
    result = await session.execute(insert_stmt)
    return bool(result.rowcount)


async def get_user_role_codes_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
) -> list[str]:
    """Возвращает коды ролей пользователя по Telegram id."""
    result = await session.execute(
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .join(User, User.id == UserRole.user_id)
        .where(User.telegram_id == telegram_id)
        .order_by(Role.code)
    )
    return list(result.scalars().all())


async def user_has_any_role_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
    role_codes: Sequence[str],
) -> bool:
    """Проверяет, есть ли у пользователя хотя бы одна роль из списка."""
    result = await session.scalar(
        select(Role.id)
        .join(UserRole, UserRole.role_id == Role.id)
        .join(User, User.id == UserRole.user_id)
        .where(
            User.telegram_id == telegram_id,
            Role.code.in_(role_codes),
        )
        .limit(1)
    )
    return result is not None


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
        update(User).values(is_bot_banned=is_private_chat_banned).where(User.telegram_id == user_id)
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
    created = bool(result.rowcount)
    if created:
        user = await get_user_by_telegram_id(session, user_id)
        if user is None:
            raise ValueError("Не удалось получить пользователя после создания")
        await assign_role_to_user(session, user.id, "user")

    await session.commit()
    return created


async def create_or_update_user_from_telegram(
    session: AsyncSession,
    telegram_id: int,
    name: str,
    language_code: str | None = None,
) -> User:
    """Создает или обновляет пользователя по данным Telegram.

    Args:
        telegram_id: внешний Telegram user id.
        name: отображаемое имя из Telegram Login Widget или бота.
        language_code: языковой код, если Telegram передал его в текущем сценарии.

    Returns:
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
    await assign_role_to_user(session, user.id, "user")
    await session.commit()
    return user
