"""Сервис пользователей."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import users as user_repository


class UsersService:
    """Бизнес-сценарии для пользователей."""

    get_internal_user_id_by_telegram_id = staticmethod(
        user_repository.get_internal_user_id_by_telegram_id
    )
    get_user_by_id = staticmethod(user_repository.get_user_by_id)
    get_user_by_telegram_id = staticmethod(user_repository.get_user_by_telegram_id)
    is_user_in_database = staticmethod(user_repository.is_user_in_database)
    create_user = staticmethod(user_repository.create_user)
    update_user_private_chat_banned = staticmethod(
        user_repository.update_user_private_chat_banned
    )
    create_user_if_not_exists = staticmethod(user_repository.create_user_if_not_exists)
    create_or_update_user_from_telegram = staticmethod(
        user_repository.create_or_update_user_from_telegram
    )


async def get_internal_user_id_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
) -> int | None:
    """Возвращает внутренний id пользователя по Telegram id."""
    return await user_repository.get_internal_user_id_by_telegram_id(session, telegram_id)


async def is_user_in_database(session: AsyncSession, user_id: int) -> bool:
    """Проверяет, существует ли пользователь с указанным Telegram id."""
    return await user_repository.is_user_in_database(session, user_id)


async def get_user_by_id(session: AsyncSession, user_id: int):
    """Возвращает пользователя по внутреннему id."""
    return await user_repository.get_user_by_id(session, user_id)


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int):
    """Возвращает пользователя по Telegram id."""
    return await user_repository.get_user_by_telegram_id(session, telegram_id)


async def create_user(
    session: AsyncSession,
    user_id: int,
    name: str,
    language_code: str | None,
) -> None:
    """Создает пользователя из данных Telegram-профиля."""
    await user_repository.create_user(session, user_id, name, language_code)


async def update_user_private_chat_banned(
    session: AsyncSession,
    user_id: int,
    is_private_chat_banned: bool,
) -> None:
    """Обновляет статус блокировки бота пользователем."""
    await user_repository.update_user_private_chat_banned(
        session,
        user_id,
        is_private_chat_banned,
    )


async def create_user_if_not_exists(
    session: AsyncSession,
    user_id: int,
    name: str,
    language_code: str | None,
) -> bool:
    """Создает пользователя из Telegram-профиля, если он еще не зарегистрирован."""
    return await user_repository.create_user_if_not_exists(session, user_id, name, language_code)


async def create_or_update_user_from_telegram(
    session: AsyncSession,
    telegram_id: int,
    name: str,
    language_code: str | None = None,
):
    """Создает или обновляет пользователя по данным Telegram."""
    return await user_repository.create_or_update_user_from_telegram(
        session,
        telegram_id,
        name,
        language_code,
    )
