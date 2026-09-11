"""Internal endpoints для сценариев Telegram-групп."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.schemas.internal.groups import (
    InternalBotCurrentGroupRedirectToggleRequest,
    InternalBotCurrentGroupRedirectToggleResponse,
    InternalBotGroupBotAdminRequest,
    InternalBotGroupBotBannedRequest,
    InternalBotGroupEnsureRequest,
    InternalBotGroupEnsureResponse,
    InternalBotGroupMigrateToSupergroupRequest,
    InternalBotRedirectGroupResponse,
    InternalBotRedirectGroupUpdateRequest,
    InternalBotTrainingResultMessageCreateRequest,
    InternalBotTrainingResultMessageUpdateRequest,
    InternalBotTrainingResultMessageUpdateResponse,
)
from app.domain.groups.service import (
    create_group_if_not_exists,
    create_group_training_result_message,
    create_group_user,
    get_all_user_redirect_groups,
    get_group_training_result_messages_id,
    get_group_user_by_user_id_and_group_id,
    get_user_group_to_redirect,
    update_group_is_bot_admin,
    update_group_is_bot_banned,
    update_group_to_supergroup,
    update_group_training_result_message_id,
    update_redirect_to_group,
)

router = APIRouter()


@router.get("/bot/groups/redirect-targets", response_model=list[int])
async def get_bot_redirect_targets(
    session: DbSession,
    telegram_id: int,
) -> list[int]:
    """Возвращает группы, куда бот должен отправить результат тренировки.

    Args:
        telegram_id: Telegram user id пользователя.

    Returns:
        список Telegram chat id групп с включенным редиректом результата.
    """
    return await get_user_group_to_redirect(session=session, user_id=telegram_id)


@router.post("/bot/groups/ensure", response_model=InternalBotGroupEnsureResponse)
async def ensure_bot_group(
    payload: InternalBotGroupEnsureRequest,
    session: DbSession,
) -> InternalBotGroupEnsureResponse:
    """Создает Telegram-группу или восстанавливает ее доступность для бота.

    Args:
        payload: Telegram chat id, название и тип группы.

    Returns:
        признак того, что группа была создана в текущем запросе.
    """
    created = await create_group_if_not_exists(
        session=session,
        id=payload.group_id,
        group_type=payload.group_type,
        name=payload.group_name,
    )
    return InternalBotGroupEnsureResponse(created=created)


@router.patch("/bot/groups/{group_id}/bot-admin")
async def update_bot_group_admin(
    group_id: int,
    payload: InternalBotGroupBotAdminRequest,
    session: DbSession,
) -> dict[str, str]:
    """Обновляет признак администратора у Telegram-бота в группе.

    Args:
        group_id: Telegram chat id группы.
        payload: новое состояние прав администратора.

    Returns:
        короткий статус успешного выполнения операции.
    """
    await update_group_is_bot_admin(
        session=session,
        group_id=group_id,
        is_bot_admin=payload.is_bot_admin,
    )
    return {"status": "ok"}


@router.patch("/bot/groups/migrate-to-supergroup")
async def migrate_bot_group_to_supergroup(
    payload: InternalBotGroupMigrateToSupergroupRequest,
    session: DbSession,
) -> dict[str, str]:
    """Переносит связи Telegram-группы на новую супергруппу.

    Args:
        payload: старый и новый Telegram chat id с данными супергруппы.

    Returns:
        короткий статус успешного выполнения операции.
    """
    await update_group_to_supergroup(
        session=session,
        group_id=payload.group_id,
        supergroup_id=payload.supergroup_id,
        supergroup_name=payload.supergroup_name,
        supergroup_type=payload.supergroup_type,
    )
    return {"status": "ok"}


@router.get(
    "/bot/groups/redirect-settings",
    response_model=list[InternalBotRedirectGroupResponse],
)
async def get_bot_redirect_settings(
    session: DbSession,
    telegram_id: int,
) -> list[InternalBotRedirectGroupResponse]:
    """Возвращает группы пользователя для меню настройки редиректа.

    Args:
        telegram_id: Telegram user id пользователя.

    Returns:
        список групп, доступных пользователю для настройки редиректа.
    """
    return await get_all_user_redirect_groups(session=session, user_id=telegram_id)


@router.post(
    "/bot/groups/redirect-settings/toggle-current",
    response_model=InternalBotCurrentGroupRedirectToggleResponse,
)
async def toggle_bot_current_group_redirect(
    payload: InternalBotCurrentGroupRedirectToggleRequest,
    session: DbSession,
) -> InternalBotCurrentGroupRedirectToggleResponse:
    """Переключает редирект результата тренировки в текущей группе.

    Args:
        payload: данные пользователя и текущей Telegram-группы.

    Returns:
        новое состояние редиректа и признак создания связи пользователя с группой.
    """
    await create_group_if_not_exists(
        session=session,
        id=payload.group_id,
        group_type=payload.group_type.upper(),
        name=payload.group_name,
    )

    group_user = await get_group_user_by_user_id_and_group_id(
        session=session,
        user_id=payload.telegram_id,
        group_id=payload.group_id,
    )
    if group_user is None:
        await create_group_user(
            session=session,
            user_id=payload.telegram_id,
            group_id=payload.group_id,
            is_user_admin=payload.is_user_admin,
            is_redirect_to_group=True,
        )
        return InternalBotCurrentGroupRedirectToggleResponse(
            is_redirect_to_group=True,
            created=True,
        )

    is_redirect_to_group = not group_user.is_redirect_to_group
    await update_redirect_to_group(
        session=session,
        group_id=payload.group_id,
        user_id=payload.telegram_id,
        is_redirect_to_group=is_redirect_to_group,
    )
    return InternalBotCurrentGroupRedirectToggleResponse(
        is_redirect_to_group=is_redirect_to_group,
        created=False,
    )


@router.patch("/bot/groups/redirect-settings")
async def update_bot_redirect_setting(
    payload: InternalBotRedirectGroupUpdateRequest,
    session: DbSession,
) -> dict[str, str]:
    """Обновляет состояние редиректа пользователя в выбранную группу.

    Args:
        payload: Telegram user id, Telegram chat id группы и новое состояние редиректа.

    Returns:
        короткий статус успешного выполнения операции.
    """
    await update_redirect_to_group(
        session=session,
        group_id=payload.group_id,
        user_id=payload.telegram_id,
        is_redirect_to_group=payload.is_redirect_to_group,
    )
    return {"status": "ok"}


@router.get("/bot/groups/{group_id}/training-results/{training_id}/message")
async def get_bot_training_result_message(
    group_id: int,
    training_id: int,
    session: DbSession,
) -> dict[str, int | None]:
    """Возвращает Telegram message id ранее отправленного результата тренировки.

    Args:
        group_id: Telegram chat id группы.
        training_id: id тренировки.

    Returns:
        JSON с `message_id` или `null`, если записи нет.
    """
    message_id = await get_group_training_result_messages_id(
        session=session,
        group_id=group_id,
        training_id=training_id,
    )
    return {"message_id": message_id}


@router.post("/bot/groups/training-result-messages")
async def create_bot_training_result_message(
    payload: InternalBotTrainingResultMessageCreateRequest,
    session: DbSession,
) -> dict[str, str]:
    """Создает запись о Telegram-сообщении результата тренировки.

    Args:
        payload: group/training/message ids для сохранения.

    Returns:
        короткий статус успешного выполнения операции.
    """
    await create_group_training_result_message(
        session=session,
        group_id=payload.group_id,
        training_id=payload.training_id,
        message_id=payload.message_id,
    )
    return {"status": "ok"}


@router.patch(
    "/bot/groups/training-result-messages",
    response_model=InternalBotTrainingResultMessageUpdateResponse,
)
async def update_bot_training_result_message(
    payload: InternalBotTrainingResultMessageUpdateRequest,
    session: DbSession,
) -> InternalBotTrainingResultMessageUpdateResponse:
    """Обновляет Telegram message id результата тренировки.

    Args:
        payload: group/training ids и новый Telegram message id.

    Returns:
        признак того, что запись была найдена и обновлена.
    """
    updated = await update_group_training_result_message_id(
        session=session,
        group_id=payload.group_id,
        training_id=payload.training_id,
        new_message_id=payload.new_message_id,
    )
    return InternalBotTrainingResultMessageUpdateResponse(updated=updated)


@router.patch("/bot/groups/{group_id}/bot-banned")
async def update_bot_group_banned(
    group_id: int,
    payload: InternalBotGroupBotBannedRequest,
    session: DbSession,
) -> dict[str, str]:
    """Обновляет признак недоступности группы для Telegram-бота.

    Args:
        group_id: Telegram chat id группы.
        payload: новый признак блокировки/удаления бота.

    Returns:
        короткий статус успешного выполнения операции.
    """
    await update_group_is_bot_banned(
        session=session,
        group_id=group_id,
        is_bot_banned=payload.is_bot_banned,
    )
    return {"status": "ok"}
