"""Единая форма добавления подходов и разбор её краткого ввода."""

import re
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from app.bot.fsm.training import (
    TrainingFlowStep,
    TrainingMode,
    TrainingStates,
    get_training_draft,
)
from app.bot.ui.training import (
    TrainingTransitionResult,
    is_current_training_callback,
    transition_training_screen,
)
from app.core.weights import format_weight, normalize_weight

router = Router()

_INDEXED_START = re.compile(r"^\s*[wrs]", re.IGNORECASE)
_INDEXED_TOKEN = re.compile(r"\s*(?P<key>[wrs])\s*(?P<value>\d+(?:[.,]\d+)?)", re.IGNORECASE)
_POSITIONAL = re.compile(
    r"^\s*(?P<weight>\d+(?:[.,]\d+)?)"
    r"(?:\s*(?:[×xх*/:])\s*|\s+)"
    r"(?P<repetitions>\d+)"
    r"(?:(?:\s*(?:[×xх*/:])\s*|\s+)(?P<sets_count>\d+))?\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class AddSetFormInput:
    """Нормализованные значения одного сообщения формы подхода."""

    weight: Decimal | None = None
    repetitions: int | None = None
    sets_count: int | None = None


@router.callback_query(F.data == "add_set", TrainingStates.menu)
async def open_add_set_form(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает форму нового подхода текущего упражнения."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.selection.mode = TrainingMode.ADD_SET.value
    next_draft.selection.exercise_id = next_draft.ui.current_exercise_id
    next_draft.selection.exercise_name = next_draft.ui.current_exercise_name
    next_draft.selection.weight = None
    next_draft.selection.repetitions = None
    next_draft.selection.sets_count = 1
    next_draft.ui.exercise_selection_return_step = None
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=(
            TrainingFlowStep.ADD_SET_FORM
            if next_draft.selection.exercise_id is not None
            else TrainingFlowStep.SELECT_EXERCISE
        ),
    )


@router.callback_query(F.data == "repeat_set", TrainingStates.menu)
async def repeat_set(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает форму с параметрами последнего сохраненного подхода."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.selection.mode = TrainingMode.ADD_SET.value
    next_draft.selection.exercise_id = next_draft.ui.current_exercise_id
    next_draft.selection.exercise_name = next_draft.ui.current_exercise_name
    next_draft.selection.weight = next_draft.ui.last_weight
    next_draft.selection.repetitions = next_draft.ui.last_repetitions
    next_draft.selection.sets_count = 1
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.ADD_SET_FORM,
    )


def parse_add_set_form_input(text: str) -> AddSetFormInput:
    """Разбирает индексированный или позиционный ввод параметров подхода.

    Args:
        text: текст из inline-результата или обычного сообщения пользователя.

    Returns:
        Набор указанных в сообщении параметров.

    Raises:
        ValueError: если формат неполный, содержит повтор индекса или некорректное
            значение количества повторений/подходов.
    """
    if _INDEXED_START.match(text):
        return _parse_indexed_input(text)

    match = _POSITIONAL.fullmatch(text)
    if match is None:
        raise ValueError(
            "Укажите w80, r8, s3 или вес и повторения в формате 80×8."
        )

    sets_count = match.group("sets_count")
    return AddSetFormInput(
        weight=_parse_weight(match.group("weight")),
        repetitions=_parse_non_negative_integer(match.group("repetitions"), "Повторения"),
        sets_count=(
            _parse_positive_integer(sets_count, "Количество подходов")
            if sets_count is not None
            else None
        ),
    )


def _parse_indexed_input(text: str) -> AddSetFormInput:
    """Разбирает последовательность w/r/s-параметров без требования порядка."""
    position = 0
    values: dict[str, str] = {}
    while position < len(text):
        match = _INDEXED_TOKEN.match(text, position)
        if match is None:
            if text[position:].strip():
                raise ValueError("Индексированный ввод содержит недопустимые символы.")
            break
        key = match.group("key").lower()
        if key in values:
            raise ValueError(f"Параметр {key} указан в сообщении больше одного раза.")
        values[key] = match.group("value")
        position = match.end()

    if not values:
        raise ValueError("Укажите хотя бы один параметр: w, r или s.")
    return AddSetFormInput(
        weight=_parse_weight(values["w"]) if "w" in values else None,
        repetitions=(
            _parse_non_negative_integer(values["r"], "Повторения")
            if "r" in values
            else None
        ),
        sets_count=(
            _parse_positive_integer(values["s"], "Количество подходов")
            if "s" in values
            else None
        ),
    )


def _parse_weight(value: str) -> Decimal:
    """Разбирает вес с десятичной запятой или точкой."""
    return normalize_weight(value.replace(",", "."))


def _parse_non_negative_integer(value: str, label: str) -> int:
    """Проверяет целое неотрицательное значение."""
    if "." in value or "," in value:
        raise ValueError(f"{label} должны быть целым числом.")
    return int(value)


def _parse_positive_integer(value: str, label: str) -> int:
    """Проверяет положительное целое значение."""
    parsed = _parse_non_negative_integer(value, label)
    if parsed < 1:
        raise ValueError(f"{label} должны быть не меньше 1.")
    return parsed


@router.inline_query(TrainingStates.add_set_form)
async def inline_add_set_form(inline_query: InlineQuery, state: FSMContext) -> None:
    """Возвращает подсказки для поля, обозначенного префиксом w/r/s."""
    query = inline_query.query.strip()
    if not query or query[0].lower() not in {"w", "r", "s"}:
        await inline_query.answer([], cache_time=0, is_personal=True)
        return

    prefix = query[0].lower()
    draft = await get_training_draft(state)
    if prefix == "s" and draft.selection.mode == TrainingMode.EDIT_SET.value:
        await inline_query.answer([], cache_time=0, is_personal=True)
        return
    substring = query[1:].strip().lower()
    results = _inline_results(prefix, substring)
    await inline_query.answer(results[:50], cache_time=0, is_personal=True)


def _inline_results(prefix: str, substring: str) -> list[InlineQueryResultArticle]:
    """Строит ограниченный набор безопасных inline-значений одного поля."""
    if prefix == "w":
        values = [normalize_weight(Decimal(number) / 4) for number in range(0, 2001)]
        return [
            InlineQueryResultArticle(
                id=f"w{value}",
                title=f"{format_weight(value)} кг",
                input_message_content=InputTextMessageContent(
                    message_text=f"w{format(value, 'f')}",
                    parse_mode=None,
                ),
            )
            for value in values
            if substring in format_weight(value).lower()
        ]

    upper_bound = 1000 if prefix == "r" else 100
    noun = "повторений" if prefix == "r" else "подходов"
    return [
        InlineQueryResultArticle(
            id=f"{prefix}{number}",
            title=f"{number} {noun}",
            input_message_content=InputTextMessageContent(
                message_text=f"{prefix}{number}",
                parse_mode=None,
            ),
        )
        for number in range(0 if prefix == "r" else 1, upper_bound + 1)
        if substring in str(number)
    ]


@router.message(F.text & ~F.text.startswith("/"), TrainingStates.add_set_form)
async def update_add_set_form(message: Message, state: FSMContext) -> None:
    """Применяет значения из сообщения к форме, не меняя остальные поля."""
    current_draft = await get_training_draft(state)
    try:
        parsed = parse_add_set_form_input(message.text)
        if (
            current_draft.selection.mode == TrainingMode.EDIT_SET.value
            and parsed.sets_count is not None
        ):
            raise ValueError("При редактировании нельзя менять количество подходов.")
    except ValueError as error:
        await message.answer(f"❌ {error}")
        return
    next_draft = deepcopy(current_draft)
    if parsed.weight is not None:
        next_draft.selection.weight = parsed.weight
    if parsed.repetitions is not None:
        next_draft.selection.repetitions = parsed.repetitions
    if parsed.sets_count is not None:
        next_draft.selection.sets_count = parsed.sets_count

    result = await transition_training_screen(
        bot=message.bot,
        chat_id=message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.ADD_SET_FORM,
    )
    if result is TrainingTransitionResult.APPLIED:
        await message.delete()


@router.callback_query(F.data == "edit_form_exercise", TrainingStates.add_set_form)
async def show_edit_form_exercise_info(callback: CallbackQuery) -> None:
    """Сообщает, что упражнение определяется выбранным подходом."""
    await callback.answer("Для изменения упражнения выберите другой подход.")
