"""Тесты Rich Message formatter-а результата тренировки для redirect-групп."""

from app.bot.formatters.redirect_training import format_redirect_training_result
from app.bot.fsm.training import (
    TrainingDraft,
    TrainingDraftData,
    TrainingDraftExercise,
    TrainingDraftSet,
)


def test_redirect_training_result_omits_empty_optional_blocks() -> None:
    """Пустой комментарий и упражнения не создают пустые Rich-блоки."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=None,
            training_date="2026-09-30",
            comment="   ",
        )
    )

    rich_message = format_redirect_training_result(
        draft,
        telegram_id=123,
        user_full_name="Егор <Плеханов>",
    )

    assert rich_message.html == (
        '<h6><a href="tg://user?id=123">Егор &lt;Плеханов&gt;</a> · Ср, 30 сентября</h6>'
    )
    assert "<blockquote>" not in rich_message.html
    assert "<table" not in rich_message.html
    assert "<footer>" not in rich_message.html


def test_redirect_training_result_formats_nonempty_blocks_without_statistics() -> None:
    """Форматтер выводит только утвержденные непустые блоки результата."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=None,
            training_date="2026-09-30",
            comment="Легкая <тренировка>",
            exercises=[
                TrainingDraftExercise(
                    exercise_id=1,
                    exercise_name="Приседания & выпады",
                    sets=[
                        TrainingDraftSet(None, 1, 80, 8),
                        TrainingDraftSet(None, 2, 80, 8),
                    ],
                ),
                TrainingDraftExercise(
                    exercise_id=2,
                    exercise_name="Пустое упражнение",
                    sets=[],
                ),
            ],
        )
    )

    rich_message = format_redirect_training_result(
        draft,
        telegram_id=123,
        user_full_name="Егор Плеханов",
    )

    assert rich_message.html is not None
    assert "<blockquote>Легкая &lt;тренировка&gt;</blockquote>" in rich_message.html
    assert "<td>Приседания &amp; выпады</td><td>80×8×2</td>" in rich_message.html
    assert "Пустое упражнение" not in rich_message.html
    assert "<footer>1 упражнение · 2 подхода</footer>" in rich_message.html
    assert "↑" not in rich_message.html
    assert "↓" not in rich_message.html
    assert "<details>" not in rich_message.html
