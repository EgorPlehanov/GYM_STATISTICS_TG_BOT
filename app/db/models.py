"""SQLAlchemy-модели проекта."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum, unique
from typing import Annotated

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.training import TRAINING_COMMENT_MAX_LENGTH
from app.db.base import Base, str_256, str_2048

intpk = Annotated[int, mapped_column(primary_key=True)]
bigintpk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]


class User(Base):
    """Пользователь системы.

    Attributes:
        id: внутренний primary key приложения.
        telegram_id: уникальный внешний идентификатор Telegram. Используется для входа через
            Telegram-бота, Telegram Login Widget и Telegram Mini App.
        name: отображаемое имя пользователя из Telegram или другого источника авторизации.
        language_code: языковой код пользователя, полученный от Telegram.
        is_bot_banned: признак того, что пользователь заблокировал бота.
        created_at: дата и время создания записи.
        updated_at: дата и время последнего обновления записи.
        trainings: тренировки пользователя.
        ratings: текущие рейтинги пользователя по упражнениям.
        roles: роли пользователя в системе.
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
    roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UserRole.user_id",
    )


class Role(Base):
    """Роль пользователя в системе.

    Attributes:
        id: внутренний primary key роли.
        code: стабильный код роли для проверок доступа.
        name: отображаемое название роли.
        description: описание назначения роли.
        created_at: дата и время создания записи.
        updated_at: дата и время последнего обновления записи.
        users: назначения роли пользователям.
    """

    __tablename__ = "role"

    id: Mapped[intpk]
    code: Mapped[str_256] = mapped_column(unique=True, index=True)
    name: Mapped[str_256]
    description: Mapped[str_2048]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    users: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )


class UserRole(Base):
    """Назначение роли пользователю.

    Attributes:
        id: внутренний primary key назначения.
        user_id: внутренний id пользователя, которому назначена роль.
        role_id: id назначенной роли.
        assigned_by_user_id: внутренний id пользователя, который назначил роль.
            `None` означает системное назначение, например bootstrap owner.
        assigned_at: дата и время назначения роли.
        user: пользователь, которому назначена роль.
        role: назначенная роль.
        assigned_by: пользователь, который назначил роль.
    """

    __tablename__ = "user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role_user_id_role_id"),)

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id", ondelete="CASCADE"))
    assigned_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
    )
    assigned_at: Mapped[created_at]

    user: Mapped["User"] = relationship(
        "User",
        back_populates="roles",
        foreign_keys=[user_id],
    )
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    assigned_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_by_user_id],
    )


class Group(Base):
    """Telegram-группа, в которую добавили бота.

    Attributes:
        id: Telegram chat id группы.
        name: название группы.
        type: тип Telegram-чата.
        is_bot_banned: признак того, что бот удален или заблокирован в группе.
        is_bot_admin: признак того, что бот является администратором группы.
        users: связи группы с пользователями.
    """

    __tablename__ = "group"

    id: Mapped[bigintpk]
    name: Mapped[str]
    type: Mapped[str_256]
    is_bot_banned: Mapped[bool] = mapped_column(default=False)
    is_bot_admin: Mapped[bool] = mapped_column(default=False)

    users: Mapped[list["GroupUser"]] = relationship("GroupUser", back_populates="group")


class GroupUser(Base):
    """Связь пользователя и Telegram-группы.

    Attributes:
        id: внутренний primary key связи.
        group_id: Telegram chat id группы.
        user_id: внутренний id пользователя.
        is_user_admin: признак того, что пользователь является администратором группы.
        is_redirect_to_group: признак включенной отправки результатов тренировок в группу.
        created_at: дата и время создания связи.
        group: связанная Telegram-группа.
        user: связанный пользователь.
    """

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
    """Сообщение с результатами тренировки в Telegram-группе.

    Attributes:
        id: внутренний primary key сообщения.
        group_id: Telegram chat id группы, куда отправлен результат.
        training_id: id тренировки, результат которой был отправлен.
        message_id: Telegram message id отправленного сообщения.
        Пара `group_id` и `training_id` уникальна.
        created_at: дата и время создания записи.
        updated_at: дата и время последнего обновления записи.
    """

    __tablename__ = "group_training_result_message"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "training_id",
            name="uq_group_training_result_message",
        ),
    )

    id: Mapped[intpk]
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("group.id", ondelete="CASCADE"))
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id", ondelete="CASCADE"))
    message_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


@unique
class MeasurementUnit(Enum):
    """Единицы измерения упражнения.

    Значения:
        KG: килограммы.
        SEC: секунды.
        MIN: минуты.
        KM: километры.
        M: метры.
    """

    KG = "кг"
    SEC = "сек"
    MIN = "мин"
    KM = "км"
    M = "м"


@unique
class ExerciseCategory(Enum):
    """Категории упражнений.

    Значения:
        NONE: категория не задана.
        CHEST: грудь.
        BACK: спина.
        BICEPS: бицепс.
        TRICEPS: трицепс.
        LEGS: ноги.
        SHOULDERS: плечи.
        ARMS: руки.
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
    """Упражнение из справочника.

    Attributes:
        id: внутренний primary key упражнения.
        name: название упражнения.
        category: категория упражнения.
        description: краткое описание упражнения.
        measurement_unit: основная единица измерения результата упражнения.
        image: ссылка или путь к изображению упражнения.
    """

    __tablename__ = "exercise"

    id: Mapped[intpk]
    name: Mapped[str_256]
    category: Mapped[ExerciseCategory | None]
    description: Mapped[str_2048]
    measurement_unit: Mapped[MeasurementUnit]
    image: Mapped[str]


class Training(Base):
    """Тренировка пользователя.

    Attributes:
        id: внутренний primary key тренировки.
        user_id: внутренний id пользователя, которому принадлежит тренировка.
        date: календарная дата тренировки без времени.
        comment: пользовательский комментарий к тренировке.
        created_at: дата и время создания записи.
        updated_at: дата и время последнего обновления записи.
        user: пользователь, которому принадлежит тренировка.
        sets: подходы, входящие в тренировку.
    """

    __tablename__ = "training"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_training_user_id_date"),
    )

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date)
    comment: Mapped[str | None] = mapped_column(String(TRAINING_COMMENT_MAX_LENGTH))
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    user: Mapped["User"] = relationship("User", back_populates="trainings")
    sets: Mapped[list["Set"]] = relationship(
        "Set",
        back_populates="training",
        cascade="all, delete-orphan",
    )


class Set(Base):
    """Подход в рамках тренировки.

    Attributes:
        id: внутренний primary key подхода.
        training_id: id тренировки, к которой относится подход.
        exercise_id: id упражнения, выполняемого в подходе.
        overall_order: порядковый номер подхода внутри всей тренировки.
        exercise_order: порядковый номер подхода внутри конкретного упражнения в тренировке.
        weight: вес или значение нагрузки в подходе.
        repetitions: количество повторений.
        execution_time: время выполнения подхода, если оно фиксировалось.
        training: тренировка, к которой относится подход.
        exercise: упражнение, выполняемое в подходе.
    """

    __tablename__ = "set"

    id: Mapped[intpk]
    training_id: Mapped[int] = mapped_column(ForeignKey("training.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id"))
    overall_order: Mapped[int]
    exercise_order: Mapped[int]
    weight: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    repetitions: Mapped[int]
    execution_time: Mapped[datetime | None]

    training: Mapped["Training"] = relationship("Training", back_populates="sets")
    exercise: Mapped["Exercise"] = relationship("Exercise")


class Rank(Base):
    """Ранг пользователя.

    Attributes:
        id: внутренний primary key ранга.
        grade: числовой уровень ранга для сортировки и сравнения.
        name: отображаемое название ранга.
    """

    __tablename__ = "rank"

    id: Mapped[intpk]
    grade: Mapped[int]
    name: Mapped[str_256]


class ExerciseRank(Base):
    """Порог ранга для конкретного упражнения или общий дефолтный порог.

    Attributes:
        id: внутренний primary key порога.
        exercise_id: id упражнения, если порог задан для конкретного упражнения.
            `None` означает общий дефолтный порог.
        rank_id: id ранга, который достигается при выполнении порога.
        level: уровень внутри ранга от 0 до 5.
        grade_threshold: минимальное значение результата для достижения порога.
        is_default: признак дефолтного порога для упражнений без специальных настроек.
        exercise: упражнение, для которого задан порог, или `None`.
        rank: ранг, связанный с порогом.
    """

    __tablename__ = "exercise_rank"
    __table_args__ = (CheckConstraint("level >= 0 AND level <= 5", name="level_check"),)

    id: Mapped[intpk]
    exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercise.id"))
    rank_id: Mapped[int] = mapped_column(ForeignKey("rank.id"))
    level: Mapped[int]
    grade_threshold: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    is_default: Mapped[bool] = mapped_column(default=False)

    exercise: Mapped["Exercise | None"] = relationship("Exercise")
    rank: Mapped["Rank"] = relationship("Rank")


class UserExerciseRating(Base):
    """Текущий рейтинг пользователя в упражнении.

    Attributes:
        id: внутренний primary key записи рейтинга.
        user_id: внутренний id пользователя.
        exercise_id: id упражнения, по которому рассчитан рейтинг.
        exercise_rank_id: id достигнутого порога ранга.
        rating_value: лучшее значение пользователя, на основе которого рассчитан рейтинг.
        created_at: дата и время создания записи.
        updated_at: дата и время последнего обновления записи.
        user: пользователь, которому принадлежит рейтинг.
        exercise: упражнение, по которому рассчитан рейтинг.
        exercise_rank: достигнутый порог ранга.
    """

    __tablename__ = "user_exercise_rating"
    __table_args__ = (UniqueConstraint("user_id", "exercise_id", name="uq_user_exercise_rating"),)

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercise.id"))
    exercise_rank_id: Mapped[int] = mapped_column(ForeignKey("exercise_rank.id"))
    rating_value: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    user: Mapped["User"] = relationship("User", back_populates="ratings")
    exercise: Mapped["Exercise | None"] = relationship("Exercise")
    exercise_rank: Mapped["ExerciseRank"] = relationship("ExerciseRank")
