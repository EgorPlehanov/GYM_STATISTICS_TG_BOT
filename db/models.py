from sqlalchemy import (
    ForeignKey, BigInteger,
    func, 
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import Annotated
from datetime import datetime
from enum import Enum, unique

from db.database import Base, str_256, str_2048


intpk = Annotated[int, mapped_column(primary_key=True)]
bigintpk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]



class User(Base):
    """
    Пользователь бота
    """
    __tablename__ = "user"

    id: Mapped[bigintpk]
    name: Mapped[str]
    language_code: Mapped[str]
    is_bot_banned: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]



class Group(Base):
    """
    Группа в которую пригласили бота
    """
    __tablename__ = "group"

    id: Mapped[bigintpk]
    name: Mapped[str]
    type: Mapped[str_256]
    is_bot_banned: Mapped[bool] = mapped_column(default=False)
    is_bot_admin: Mapped[bool] = mapped_column(default=False)



class GroupUser(Base):
    """
    Пользователи в группе
    """
    __tablename__ = "group_user"

    id: Mapped[intpk]
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    is_user_admin: Mapped[bool] = mapped_column(default=False)
    is_redirect_to_group: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[created_at]



class GroupTrainingResultMessage(Base):
    """
    Сообщение с результатами тренировки в группе
    """
    __tablename__ = "group_training_result_message"

    id: Mapped[intpk]
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id", ondelete="CASCADE"))
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id", ondelete="CASCADE"))
    message_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]



@unique
class MeasurementUnit(Enum):
    """
    Единицы измерения
    """
    KG = "кг"
    SEC = "сек"
    MIN = "мин"
    KM = "км"
    M = "м"



@unique
class ExerciseCategory(Enum):
    """
    Категории упражнений
    """
    NONE = None
    CHEST = "грудь"
    BACK = "спина"
    BICEPS = "бицепс"
    TRICEPS = "трицепс"
    LEGS = "ноги"
    SHOULDERS = "плечи"
    ARMS = "руки"



class Exercise(Base):
    """
    Упражнение
    """
    __tablename__ = "exercise"

    id: Mapped[intpk]
    name: Mapped[str_256]
    category: Mapped[ExerciseCategory | None]
    description: Mapped[str_2048]
    measurement_unit: Mapped[MeasurementUnit]
    image: Mapped[str]



class Training(Base):
    """
    Тренировка
    """
    __tablename__ = "training"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    date: Mapped[datetime]
    comment: Mapped[str_256 | None]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    sets: Mapped[list["Set"]] = relationship("Set", back_populates="training")



class Set(Base):
    """
    Подход на упражнение в тренировке
    """
    __tablename__ = "set"

    id: Mapped[intpk]
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id"))
    overall_order: Mapped[int] # Порядковый номер подхода на всей тренировке
    exercise_order: Mapped[int] # Порядковый номер подхода для конкретного упражнения
    weight: Mapped[float]
    repetitions: Mapped[int]
    execution_time: Mapped[datetime | None]

    training: Mapped["Training"] = relationship("Training", back_populates="sets", overlaps="sets")



class Rank(Base):
    """
    Ранг
    """
    __tablename__ = "rank"

    id: Mapped[intpk]
    grade: Mapped[int]
    name: Mapped[str_256]



class ExerciseRank(Base):
    """
    Ранг упражнения
    """
    __tablename__ = "exercise_rank"

    id: Mapped[intpk]
    exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercise.id"))
    rank_id: Mapped[int] = mapped_column(ForeignKey("rank.id"))
    level: Mapped[int]
    grade_threshold: Mapped[float]
    is_default: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        CheckConstraint('level >= 0 AND level <= 5', name='level_check'),
    )



class UserExerciseRating(Base):
    """
    Ранг пользователя в упражнении
    """
    __tablename__ = "user_exercise_rating"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercise.id"))
    exercise_rank_id: Mapped[int] = mapped_column(ForeignKey("exercise_rank.id"))
    rating_value: Mapped[float]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
