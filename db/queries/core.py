from sqlalchemy import text

from db.database import async_engine, sync_engine, Base, sync_session_factory, async_session_factory
from db.models import *



async def create_tables_async():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)



def create_exercises_values_sync():
    exercises_data = [
        {
            'name': 'Жим лежа', 'category': 'CHEST',
            'description': 'Упражнение на развитие грудных мышц',
            'measurement_unit': 'KG', 'image': 'ссылка_на_изображение_1'
        },
        {
            'name': 'Горизонтальная тяга', 'category': 'BACK',
            'description': 'Упражнение на развитие спины',
            'measurement_unit': 'KG', 'image': 'ссылка_на_изображение_2'
        },
        {
            'name': 'Присед', 'category': 'LEGS',
            'description': 'Упражнение на развитие ног',
            'measurement_unit': 'KG', 'image': 'ссылка_на_изображение_3'
        },
        {
            'name': 'Отжимания на брусьях', 'category': 'TRICEPS',
            'description': 'Упражнение на развитие трицепса',
            'measurement_unit': 'KG', 'image': 'ссылка_на_изображение_4'
        },
        {
            'name': 'Подтягивания на турнике', 'category': 'BACK',
            'description': 'Упражнение на развитие спины и бицепса',
            'measurement_unit': 'KG', 'image': 'ссылка_на_изображение_5'
        },
        {
            'name': 'Становая тяга', 'category': 'BACK',
            'description': 'Упражнение на развитие спины и ног',
            'measurement_unit': 'KG', 'image': 'ссылка_на_изображение_6'
        }
    ]
    with sync_session_factory() as session:
        for exercise_data in exercises_data:
            exercise = Exercise(**exercise_data)
            session.add(exercise)

        session.commit()



def create_tables_sync():
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    create_exercises_values_sync()

    print('БД ПЕРЕСОЗДАНА')

