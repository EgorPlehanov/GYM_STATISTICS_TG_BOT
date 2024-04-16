from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine, String

from typing import Annotated

from config_reader import config



sync_engine = create_engine(
    url=config.DB_URL_SYNC,
    # echo=True,
)



async_engine = create_async_engine(
    url=config.DB_URL_ASYNC,
    # echo=True,
)



sync_session_factory = sessionmaker(sync_engine)
async_session_factory = async_sessionmaker(async_engine)



str_256 = Annotated[str, 256]
str_2048 = Annotated[str, 2048]



class Base(DeclarativeBase):
    type_annatation_map = {
        str_256: String(256),
        str_2048: String(2048)
    }