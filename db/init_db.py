import sys
import os

# Добавить путь к вашему проекту в переменную PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.append(project_dir)

from db.database import Base, sync_engine
from db.queries.core import create_exercises_values_sync



def create_tables_sync():
    # Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    create_exercises_values_sync()

    # Создание таблиц по одной
    # Base.metadata.create_all(sync_engine, tables=[Rank.__table__])
    # Base.metadata.create_all(sync_engine, tables=[ExerciseRank.__table__])
    # Base.metadata.create_all(sync_engine, tables=[UserExerciseRating.__table__])

    print('РАБОТА С БД ЗАВЕРШЕНА')



if __name__ == '__main__':
    create_tables_sync()