from sqlalchemy import text

from db.database import async_engine, sync_engine, Base, sync_session_factory, async_session_factory
from db.models import *



async def create_tables_async():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)



def create_tables_sync():
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
