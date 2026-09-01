"""SQLAlchemy-модели проекта."""

from datetime import datetime
from enum import Enum, unique
from typing import Annotated

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, str_2048, str_256


intpk = Annotated[int, mapped_column(primary_key=True)]
bigintpk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]


class User(Base):
    """Пользователь системы.

    `id` - внутренний ключ приложения.
    `telegram_id` - внешний идентификатор Telegram, который используется для входа через бота,
    Telegram Login Widget и Telegram Mini App.
    """

    __tablename__ = "user"

    id: Mapped[intpk]
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str]
    language_code: Mapped[str | None]
    is_bot_banned: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    trainings: Mapped[list["Training"]] = relationship("Training", back_populates="user")
    ratings: Mapped[list["UserExerciseRating"]] = relationship(
        "UserExerciseRating",
        back_populates="user",
    )


class Group(Base):
    """Telegram-группа, в которую добавили бота."""

    __tablename__ = "group"

    id: Mapped[bigintpk]
    name: Mapped[str]
    type: Mapped[str_256]
    is_bot_banned: Mapped[bool] = mapped_column(default=False)
    is_bot_admin: Mapped[bool] = mapped_column(default=False)

    users: Mapped[list["GroupUser"]] = relationship("GroupUser", back_populates="group")


class GroupUser(Base):
    """Связь пользователя и Telegram-группы."""

    __tablename__ = "group_user"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user_group_id_user_id"),
    )

    id: Mapped[intpk]
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("group.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    is_user_admin: Mapped[bool] = mapped_column(default=False)
    is_redirect_to_group: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[created_at]

    group: Mapped["Group"] = relationship("Group", back_populates="users")
    user: Mapped["User"] = relationship("User")


class GroupTrainingResultMessage(Base):
    """Сообщение с результатами тренировки в Telegram-группе."""

    __tablename__ = "group_training_result_message"

    id: Mapped[intpk]
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("group.id", ondelete="CASCADE"))
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id", ondelete="CASCADE"))
    message_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


@unique
class MeasurementUnit(Enum):
    """Единицы измерения упражнения."""

    KG = "кг"
    SEC = "сек"
    MIN = "мин"
    KM = "км"
    M = "м"


@unique
class ExerciseCategory(Enum):
    """Категории упражнений."""

    NONE = None
    CHEST = "грудь"
    BACK = "спина"
    BICEPS = "бицепс"
    TRICEPS = "трицепс"
    LEGS = "ноги"
    SHOULDERS = "плечи"
    ARMS = "руки"


class Exercise(Base):
    """Упражнение из справочника."""

    __tablename__ = "exercise"

    id: Mapped[intpk]
    name: Mapped[str_256]
    category: Mapped[ExerciseCategory | None]
    description: Mapped[str_2048]
    measurement_unit: Mapped[MeasurementUnit]
    image: Mapped[str]


class Training(Base):
    """Тренировка пользователя."""

    __tablename__ = "training"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    date: Mapped[datetime]
    comment: Mapped[str_256 | None]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    user: Mapped["User"] = relationship("User", back_populates="trainings")
    sets: Mapped[list["Set"]] = relationship(
        "Set",
        back_populates="training",
        cascade="all, delete-orphan",
    )


class Set(Base):
    """Подход в рамках тренировки."""

    __tablename__ = "set"

    id: Mapped[intpk]
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id"))
    overall_order: Mapped[int]
    exercise_order: Mapped[int]
    weight: Mapped[float]
    repetitions: Mapped[int]
    execution_time: Mapped[datetime | None]

    training: Mapped["Training"] = relationship("Training", back_populates="sets")
    exercise: Mapped["Exercise"] = relationship("Exercise")


class Rank(Base):
    """Ранг пользователя."""

    __tablename__ = "rank"

    id: Mapped[intpk]
    grade: Mapped[int]
    name: Mapped[str_256]


class ExerciseRank(Base):
    """Порог ранга для конкретного упражнения или общий дефолтный порог."""

    __tablename__ = "exercise_rank"
    __table_args__ = (
        CheckConstraint("level >= 0 AND level <= 5", name="level_check"),
    )

    id: Mapped[intpk]
    exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercise.id"))
    rank_id: Mapped[int] = mapped_column(ForeignKey("rank.id"))
    level: Mapped[int]
    grade_threshold: Mapped[float]
    is_default: Mapped[bool] = mapped_column(default=False)

    exercise: Mapped["Exercise | None"] = relationship("Exercise")
    rank: Mapped["Rank"] = relationship("Rank")


class UserExerciseRating(Base):
    """Текущий рейтинг пользователя в упражнении."""

    __tablename__ = "user_exercise_rating"
    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", name="uq_user_exercise_rating"),
    )

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercise.id"))
    exercise_rank_id: Mapped[int] = mapped_column(ForeignKey("exercise_rank.id"))
    rating_value: Mapped[float]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    user: Mapped["User"] = relationship("User", back_populates="ratings")
    exercise: Mapped["Exercise | None"] = relationship("Exercise")
    exercise_rank: Mapped["ExerciseRank"] = relationship("ExerciseRank")
