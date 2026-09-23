"""Проверки сохранения при явной замене занятой даты."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.db.repositories import trainings as training_repository


async def test_new_draft_replaces_conflict_only_at_save(monkeypatch) -> None:
    """Новый черновик создаётся после удаления конфликта в одной транзакции."""
    session = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    calls = []

    async def fake_delete_training_for_user(**kwargs) -> None:
        calls.append(("delete", kwargs))

    async def fake_get_internal_user_id_or_raise(**_kwargs) -> int:
        return 1

    async def fake_save_new_training_data(_session, _training_data) -> int:
        calls.append(("create", None))
        return 42

    async def fake_delete_old_sets(_session, _training_id, _set_ids) -> bool:
        return False

    monkeypatch.setattr(
        training_repository, "_delete_training_for_user", fake_delete_training_for_user
    )
    monkeypatch.setattr(
        training_repository,
        "_get_internal_user_id_or_raise",
        fake_get_internal_user_id_or_raise,
    )
    monkeypatch.setattr(
        training_repository, "save_new_training_data", fake_save_new_training_data
    )
    monkeypatch.setattr(training_repository, "delete_old_sets", fake_delete_old_sets)

    result = await training_repository.save_training_data(
        session,
        {"id": None, "user_id": 1, "date": date(2026, 9, 2), "exercises": {}},
        replace_training_id=20,
    )

    assert result == (42, False, True)
    assert calls == [
        (
            "delete",
            {
                "session": session,
                "training_id": 20,
                "internal_user_id": 1,
                "training_date": date(2026, 9, 2),
            },
        ),
        ("create", None),
    ]
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


async def test_saved_draft_checks_owner_then_replaces_conflict(monkeypatch) -> None:
    """Сохраненная тренировка заменяет конфликт только после проверки владельца."""
    session = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    calls = []

    async def fake_get_internal_user_id_or_raise(**_kwargs) -> int:
        return 1

    async def fake_ensure_training_belongs_to_user(**kwargs) -> None:
        calls.append(("ensure_source", kwargs))

    async def fake_delete_training_for_user(**kwargs) -> None:
        calls.append(("delete_conflict", kwargs))

    async def fake_update_training_data(*_args) -> bool:
        calls.append(("update_source", None))
        return True

    async def fake_delete_old_sets(_session, _training_id, _set_ids) -> bool:
        return False

    monkeypatch.setattr(
        training_repository,
        "_get_internal_user_id_or_raise",
        fake_get_internal_user_id_or_raise,
    )
    monkeypatch.setattr(
        training_repository,
        "_ensure_training_belongs_to_user",
        fake_ensure_training_belongs_to_user,
    )
    monkeypatch.setattr(
        training_repository,
        "_delete_training_for_user",
        fake_delete_training_for_user,
    )
    monkeypatch.setattr(
        training_repository,
        "update_training_data",
        fake_update_training_data,
    )
    monkeypatch.setattr(training_repository, "delete_old_sets", fake_delete_old_sets)

    result = await training_repository.save_training_data(
        session,
        {"id": 10, "user_id": 1, "date": date(2026, 9, 2), "exercises": {}},
        replace_training_id=20,
    )

    assert result == (10, True, False)
    assert [name for name, _ in calls] == [
        "ensure_source",
        "delete_conflict",
        "update_source",
    ]
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


async def test_failed_replacement_rolls_back_conflict_deletion(monkeypatch) -> None:
    """Ошибка создания новой тренировки откатывает удаление конфликта."""
    session = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    calls = []

    async def fake_get_internal_user_id_or_raise(**_kwargs) -> int:
        return 1

    async def fake_delete_training_for_user(**_kwargs) -> None:
        calls.append("delete")

    async def failed_save_new_training_data(_session, _training_data) -> int:
        raise RuntimeError("Ошибка вставки тренировки")

    monkeypatch.setattr(
        training_repository,
        "_get_internal_user_id_or_raise",
        fake_get_internal_user_id_or_raise,
    )
    monkeypatch.setattr(
        training_repository,
        "_delete_training_for_user",
        fake_delete_training_for_user,
    )
    monkeypatch.setattr(
        training_repository,
        "save_new_training_data",
        failed_save_new_training_data,
    )

    with pytest.raises(RuntimeError, match="Ошибка вставки тренировки"):
        await training_repository.save_training_data(
            session,
            {"id": None, "user_id": 1, "date": date(2026, 9, 2), "exercises": {}},
            replace_training_id=20,
        )

    assert calls == ["delete"]
    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()
