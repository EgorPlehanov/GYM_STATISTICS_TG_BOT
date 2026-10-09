"""Тесты подготовки комментария тренировки к inline-отправке."""

from app.bot.handlers.training_units.finish import _build_inline_comment_result
from app.core.training import TRAINING_COMMENT_MAX_LENGTH


def test_inline_comment_result_contains_current_length() -> None:
    """Inline-результат сообщает текущую длину комментария."""
    result = _build_inline_comment_result("Заметка")

    assert result.description == f"7/{TRAINING_COMMENT_MAX_LENGTH} символов"
    assert result.input_message_content.message_text == "Заметка"


def test_inline_comment_result_truncates_text_to_database_limit() -> None:
    """Inline-результат заранее ограничивает текст лимитом поля базы данных."""
    comment = "а" * (TRAINING_COMMENT_MAX_LENGTH + 1)
    result = _build_inline_comment_result(comment)

    assert result.description == (
        f"{TRAINING_COMMENT_MAX_LENGTH + 1}/{TRAINING_COMMENT_MAX_LENGTH} символов: "
        f"будет сохранено {TRAINING_COMMENT_MAX_LENGTH}"
    )
    assert result.input_message_content.message_text == "а" * TRAINING_COMMENT_MAX_LENGTH
