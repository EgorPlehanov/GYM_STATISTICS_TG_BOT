"""Команда загрузки справочных данных."""

import json
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.db.models import ExerciseCategory, MeasurementUnit
from app.db.session import sync_engine, sync_session_factory


SEED_DATA_DIR = Path(__file__).with_name("seed_data")


def _normalize_seed_value(key: str, value: Any) -> Any:
    """Преобразует строковые значения JSON в типы, ожидаемые SQLAlchemy-моделями.

    Вход: имя поля из seed JSON и его исходное значение.
    Выход: значение, которое можно передать в SQLAlchemy insert.
    """
    if value is None:
        return None
    if key == "category":
        return ExerciseCategory[value]
    if key == "measurement_unit":
        return MeasurementUnit[value]
    return value


def _load_json_seed(file_path: Path) -> list[dict[str, Any]]:
    """Читает JSON-файл справочника и возвращает список записей."""
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def seed_reference_data(session: Session) -> None:
    """Загружает справочники в существующие таблицы.

    Запись считается уже существующей, если в таблице есть строка с таким же набором
    значений по всем полям, кроме `id`.
    """
    from app.db.base import Base

    inspector = inspect(sync_engine)

    for table in Base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue

        file_path = SEED_DATA_DIR / f"{table.name}.json"
        if not file_path.exists():
            continue

        for item in _load_json_seed(file_path):
            values = {
                key: _normalize_seed_value(key, value)
                for key, value in item.items()
            }
            conditions = [
                table.c[key] == value
                for key, value in values.items()
                if key != "id"
            ]

            existing_record = session.execute(select(table).where(*conditions)).fetchone()
            if existing_record is None:
                session.execute(table.insert().values(values))

    session.commit()


def main() -> None:
    """Точка входа CLI-команды загрузки справочников."""
    with sync_session_factory() as session:
        seed_reference_data(session)


if __name__ == "__main__":
    main()
