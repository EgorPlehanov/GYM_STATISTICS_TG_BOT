"""Тесты репозитория Telegram-групп."""

import pytest


@pytest.mark.asyncio
async def test_update_group_to_supergroup_creates_group_before_relations_update():
    """Проверяет порядок переноса связей при миграции группы в супергруппу."""
    from app.db.repositories.groups import update_group_to_supergroup

    session = FakeSession()

    await update_group_to_supergroup(
        session=session,
        group_id=-5349120957,
        supergroup_id=-1004446951947,
        supergroup_name="Тестовая группа",
        supergroup_type="supergroup",
    )

    assert session.statement_tables == [
        ("Insert", "group"),
        ("Update", "group_user"),
        ("Update", "group_training_result_message"),
        ("Delete", "group"),
    ]
    assert session.is_committed is True


class FakeSession:
    """Тестовая заглушка SQLAlchemy session, которая фиксирует SQL statements."""

    def __init__(self) -> None:
        """Создает пустой список выполненных SQL statements."""
        self.statements = []
        self.is_committed = False

    async def execute(self, statement) -> None:
        """Сохраняет statement без обращения к базе данных.

        Args:
            statement: SQLAlchemy statement, который должен был быть выполнен.
        """
        self.statements.append(statement)

    async def commit(self) -> None:
        """Фиксирует факт commit-а."""
        self.is_committed = True

    @property
    def statement_tables(self) -> list[tuple[str, str]]:
        """Возвращает тип statement и имя таблицы для проверки порядка операций."""
        return [
            (statement.__class__.__name__, statement.table.name)
            for statement in self.statements
        ]
