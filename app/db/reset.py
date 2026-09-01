"""Dev-команда полного сброса базы данных."""

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.core.config import config
from app.db.seed import seed_reference_data
from app.db.session import sync_engine, sync_session_factory


def _ensure_dev_environment() -> None:
    """Запрещает сброс базы вне dev-окружения."""
    if config.APP_ENV != "dev":
        raise RuntimeError("Сброс базы разрешен только при APP_ENV=dev")


def reset_database() -> None:
    """Полностью пересоздает схему БД, применяет миграции и загружает справочники.

    Выходных параметров нет. При ошибке подключения, миграции или seed-команды
    исключение пробрасывается выше, чтобы Docker/CI явно увидели неуспешный запуск.
    """
    _ensure_dev_environment()

    with sync_engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")

    with sync_session_factory() as session:
        seed_reference_data(session)


def main() -> None:
    """Точка входа CLI-команды сброса БД."""
    reset_database()


if __name__ == "__main__":
    main()
