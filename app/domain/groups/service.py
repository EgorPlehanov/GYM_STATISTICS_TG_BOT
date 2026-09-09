"""Сервис Telegram-групп."""


from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import groups as group_repository

RedirectGroup = group_repository.RedirectGroup


class GroupsService:
    """Бизнес-сценарии для Telegram-групп."""

    is_group_in_database = staticmethod(group_repository.is_group_in_database)
    create_group = staticmethod(group_repository.create_group)
    update_group_is_bot_banned = staticmethod(group_repository.update_group_is_bot_banned)
    create_group_if_not_exists = staticmethod(group_repository.create_group_if_not_exists)
    update_group_is_bot_admin = staticmethod(group_repository.update_group_is_bot_admin)
    update_group_to_supergroup = staticmethod(group_repository.update_group_to_supergroup)
    check_user_in_group = staticmethod(group_repository.check_user_in_group)
    get_group_user_by_user_id_and_group_id = staticmethod(
        group_repository.get_group_user_by_user_id_and_group_id
    )
    create_group_user = staticmethod(group_repository.create_group_user)
    update_redirect_to_group = staticmethod(group_repository.update_redirect_to_group)
    get_all_user_redirect_groups = staticmethod(group_repository.get_all_user_redirect_groups)
    get_user_group_to_redirect = staticmethod(group_repository.get_user_group_to_redirect)
    update_group_user_is_admin = staticmethod(group_repository.update_group_user_is_admin)
    delete_group_user = staticmethod(group_repository.delete_group_user)
    create_group_training_result_message = staticmethod(
        group_repository.create_group_training_result_message
    )
    get_group_training_result_messages_id = staticmethod(
        group_repository.get_group_training_result_messages_id
    )
    update_group_training_result_message_id = staticmethod(
        group_repository.update_group_training_result_message_id
    )


async def is_group_in_database(session: AsyncSession, user_id: int) -> bool:
    """Проверяет, существует ли группа в базе данных."""
    return await group_repository.is_group_in_database(session, user_id)


async def create_group(session: AsyncSession, id: int, name: str, type: str) -> None:
    """Добавляет Telegram-группу в базу данных."""
    await group_repository.create_group(session, id, name, type)


async def update_group_is_bot_banned(
    session: AsyncSession,
    group_id: int,
    is_bot_banned: bool,
) -> None:
    """Обновляет статус блокировки бота в группе."""
    await group_repository.update_group_is_bot_banned(session, group_id, is_bot_banned)


async def create_group_if_not_exists(
    session: AsyncSession,
    id: int,
    group_type: str,
    name: str,
) -> bool:
    """Создает Telegram-группу, если ее еще нет."""
    return await group_repository.create_group_if_not_exists(session, id, group_type, name)


async def update_group_is_bot_admin(
    session: AsyncSession,
    group_id: int,
    is_bot_admin: bool,
) -> None:
    """Обновляет статус администратора бота в группе."""
    await group_repository.update_group_is_bot_admin(session, group_id, is_bot_admin)


async def update_group_to_supergroup(
    session: AsyncSession,
    group_id: int,
    supergroup_id: int,
    supergroup_name: str,
    supergroup_type: str,
) -> None:
    """Переносит связи старой группы на супергруппу."""
    await group_repository.update_group_to_supergroup(
        session,
        group_id,
        supergroup_id,
        supergroup_name,
        supergroup_type,
    )


async def check_user_in_group(session: AsyncSession, user_id: int, group_id: int) -> bool:
    """Проверяет, состоит ли пользователь в группе."""
    return await group_repository.check_user_in_group(session, user_id, group_id)


async def get_group_user_by_user_id_and_group_id(
    session: AsyncSession,
    user_id: int,
    group_id: int,
):
    """Возвращает связь пользователя и группы."""
    return await group_repository.get_group_user_by_user_id_and_group_id(session, user_id, group_id)


async def create_group_user(
    session: AsyncSession,
    user_id: int,
    group_id: int,
    is_user_admin: bool,
    is_redirect_to_group: bool = False,
) -> bool:
    """Добавляет пользователя в группу."""
    return await group_repository.create_group_user(
        session,
        user_id,
        group_id,
        is_user_admin,
        is_redirect_to_group,
    )


async def update_redirect_to_group(
    session: AsyncSession,
    user_id: int,
    group_id: int,
    is_redirect_to_group: bool,
) -> None:
    """Обновляет статус редиректа результатов в группу."""
    await group_repository.update_redirect_to_group(
        session,
        user_id,
        group_id,
        is_redirect_to_group,
    )


async def get_all_user_redirect_groups(
    session: AsyncSession,
    user_id: int,
) -> list[RedirectGroup]:
    """Возвращает группы пользователя, доступные для настройки редиректа."""
    return await group_repository.get_all_user_redirect_groups(session, user_id)


async def get_user_group_to_redirect(session: AsyncSession, user_id: int) -> list[int]:
    """Возвращает id групп, куда включен редирект результатов пользователя."""
    return await group_repository.get_user_group_to_redirect(session, user_id)


async def update_group_user_is_admin(
    session: AsyncSession,
    group_id: int,
    user_id: int,
    is_admin: bool,
) -> None:
    """Обновляет статус администратора пользователя в группе."""
    await group_repository.update_group_user_is_admin(session, group_id, user_id, is_admin)


async def delete_group_user(session: AsyncSession, group_id: int, user_id: int) -> None:
    """Удаляет пользователя из группы."""
    await group_repository.delete_group_user(session, group_id, user_id)


async def create_group_training_result_message(
    session: AsyncSession,
    group_id: int,
    training_id: int,
    message_id: int,
) -> None:
    """Создает запись о сообщении с результатом тренировки."""
    await group_repository.create_group_training_result_message(
        session,
        group_id,
        training_id,
        message_id,
    )


async def get_group_training_result_messages_id(
    session: AsyncSession,
    group_id: int,
    training_id: int,
) -> int | None:
    """Возвращает Telegram message id результата тренировки в группе."""
    return await group_repository.get_group_training_result_messages_id(
        session,
        group_id,
        training_id,
    )


async def update_group_training_result_message_id(
    session: AsyncSession,
    group_id: int,
    training_id: int,
    new_message_id: int,
) -> bool:
    """Обновляет Telegram message id результата тренировки в группе."""
    return await group_repository.update_group_training_result_message_id(
        session,
        group_id,
        training_id,
        new_message_id,
    )
