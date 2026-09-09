"""Начальная схема базы данных.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


exercise_category_enum = postgresql.ENUM(
    "NONE",
    "CHEST",
    "BACK",
    "BICEPS",
    "TRICEPS",
    "LEGS",
    "SHOULDERS",
    "ARMS",
    name="exercisecategory",
    create_type=False,
)
measurement_unit_enum = postgresql.ENUM(
    "KG",
    "SEC",
    "MIN",
    "KM",
    "M",
    name="measurementunit",
    create_type=False,
)


def upgrade() -> None:
    """Создает начальную структуру таблиц."""
    exercise_category_enum.create(op.get_bind(), checkfirst=True)
    measurement_unit_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("language_code", sa.String(), nullable=True),
        sa.Column("is_bot_banned", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_telegram_id"), "user", ["telegram_id"], unique=True)

    op.create_table(
        "group",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(length=256), nullable=False),
        sa.Column("is_bot_banned", sa.Boolean(), nullable=False),
        sa.Column("is_bot_admin", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "exercise",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("category", exercise_category_enum, nullable=True),
        sa.Column("description", sa.String(length=2048), nullable=False),
        sa.Column("measurement_unit", measurement_unit_enum, nullable=False),
        sa.Column("image", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rank",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "group_user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("is_user_admin", sa.Boolean(), nullable=False),
        sa.Column("is_redirect_to_group", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["group.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_user_group_id_user_id"),
    )

    op.create_table(
        "training",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("comment", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "exercise_rank",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=True),
        sa.Column("rank_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("grade_threshold", sa.Float(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.CheckConstraint("level >= 0 AND level <= 5", name="level_check"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercise.id"]),
        sa.ForeignKeyConstraint(["rank_id"], ["rank.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "set",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("training_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("overall_order", sa.Integer(), nullable=False),
        sa.Column("exercise_order", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("execution_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercise.id"]),
        sa.ForeignKeyConstraint(["training_id"], ["training.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "group_training_result_message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("training_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["group.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["training_id"], ["training.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_exercise_rating",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=True),
        sa.Column("exercise_rank_id", sa.Integer(), nullable=False),
        sa.Column("rating_value", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercise.id"]),
        sa.ForeignKeyConstraint(["exercise_rank_id"], ["exercise_rank.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "exercise_id", name="uq_user_exercise_rating"),
    )


def downgrade() -> None:
    """Удаляет начальную структуру таблиц."""
    op.drop_table("user_exercise_rating")
    op.drop_table("group_training_result_message")
    op.drop_table("set")
    op.drop_table("exercise_rank")
    op.drop_table("training")
    op.drop_table("group_user")
    op.drop_table("rank")
    op.drop_table("exercise")
    op.drop_table("group")
    op.drop_index(op.f("ix_user_telegram_id"), table_name="user")
    op.drop_table("user")

    measurement_unit_enum.drop(op.get_bind(), checkfirst=True)
    exercise_category_enum.drop(op.get_bind(), checkfirst=True)
