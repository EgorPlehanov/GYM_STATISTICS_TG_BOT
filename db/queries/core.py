from sqlalchemy import text, select, inspect, DDL

import json
import os

from db.database import (
    Base,
    async_engine, sync_engine,
    sync_session_factory, async_session_factory
)
from db.models import *



async def create_tables_async():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)



def create_exercises_values_sync():
    """
    Загрузка данных из JSON-файла в базу данных
    """
    data_folder = 'db/data'
    tables = [table for table  in Base.metadata.tables.values()]

    with sync_session_factory() as session:
        for table in tables:
            # Проверка существования таблицы в базе данных
            if not inspect(sync_engine).has_table(table.name):
                table.create(sync_engine)
                
            file_path = os.path.join(data_folder, f"{table.name}.json")

            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                for item in data:
                    # Генерация динамического условия для сравнения полей в таблице
                    conditions = [
                        getattr(table.c, key) == value
                        for key, value in item.items()
                        if key != 'id'
                    ]

                    select_query = select(table).where(*conditions)

                    existing_record = session.execute(select_query).fetchone()

                    if not existing_record:
                        session.execute(table.insert().values(item))

        session.commit()
