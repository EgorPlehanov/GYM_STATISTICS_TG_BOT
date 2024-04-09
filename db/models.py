from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from typing import Annotated
from datetime import datetime
from enum import Enum, unique

from db.database import Base, str_256, str_4096



intpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]



class User(Base):
    __tablename__ = "user"

    id: Mapped[intpk]
    name: Mapped[str]
    chat_id: Mapped[int]
    language_code: Mapped[str]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]



class Group(Base):
    __tablename__ = "group"

    id: Mapped[intpk]
    name: Mapped[str]



class UserGroup(Base):
    __tablename__ = "user_group"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    is_user_admin: Mapped[bool]
    created_at: Mapped[created_at]



class Training(Base):
    __tablename__ = "training"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    date: Mapped[datetime]
    comment: Mapped[str_256]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]



@unique
class MeasurementUnit(Enum):
    KG = "кг"
    SEC = "сек"
    MIN = "мин"
    KM = "км"
    M = "м"



@unique
class ExerciseCategory(Enum):
    NONE = None
    CHEST = "грудь"
    BACK = "спина"
    BICEPS = "бицепс"
    TRICEPS = "трицепс"
    LEGS = "ноги"
    SHOULDERS = "плечи"
    ARMS = "руки"



class Exercise(Base):
    __tablename__ = "exercise"

    id: Mapped[intpk]
    name: Mapped[str_256]
    category: Mapped[ExerciseCategory | None]
    discription: Mapped[str_4096]
    measurement_unit: Mapped[MeasurementUnit]
    image: Mapped[str]



class Set(Base):
    __tablename__ = "set"

    id: Mapped[intpk]
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id"))
    overall_order: Mapped[int] # Порядковый номер подхода на всей тренировке
    exercise_order: Mapped[int] # Порядковый номер подхода для конкретного упражнения
    weight: Mapped[float]
    repetitions: Mapped[int]
    execution_time: Mapped[datetime | None]










# metadata_obj = MetaData()



# user = Table(
#     "user",
#     metadata_obj,
#     Column("id", Integer, primary_key=True),
#     Column("name", String),
#     Column("chat_id", Integer),
#     Column("language_code", String),
#     Column("created_at", DateTime),
#     Column("updated_at", DateTime),
# )



# group = Table(
#     "group",
#     metadata_obj,
#     Column("id", Integer, primary_key=True),
#     Column("name", String),
# )



# user_group = Table(
#     "user_group",
#     metadata_obj,
#     Column("id", Integer, primary_key=True),
#     Column("user_id", Integer),
#     Column("group_id", Integer),
#     Column("is_user_admin", Boolean),
# )



# training = Table(
#     "training",
#     metadata_obj,
#     Column("id", Integer, primary_key=True),
#     Column("user_id", Integer),
#     Column("date", DateTime),
#     Column("created_at", DateTime),
# )



# exercise = Table(
#     "exercise",
#     metadata_obj,
# )
