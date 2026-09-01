"""Совместимая команда инициализации БД для старого Docker entrypoint.

Новая production-схема должна использовать Alembic-миграции и `app.db.seed`.
"""

from app.db.base import Base
from app.db.seed import seed_reference_data
from app.db.session import sync_engine, sync_session_factory

def create_tables_sync():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        seed_reference_data(session)

    print('РАБОТА С БД ЗАВЕРШЕНА')



if __name__ == '__main__':
    create_tables_sync()
