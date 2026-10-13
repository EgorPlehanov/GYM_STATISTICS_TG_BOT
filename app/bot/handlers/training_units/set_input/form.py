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

_MIN_WEIGHT = Decimal("0")
_MAX_WEIGHT = Decimal("500")
_WEIGHT_STEP = Decimal("0.25")
_MIN_REPETITIONS = 0
_MAX_REPETITIONS = 1000
_MIN_SETS_COUNT = 1
_MAX_SETS_COUNT = 100


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
            TrainingFlowStep.SET_FORM
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
        next_step=TrainingFlowStep.SET_FORM,
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
        repetitions=_parse_repetitions(match.group("repetitions")),
        sets_count=(
            _parse_sets_count(sets_count)
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
            _parse_repetitions(values["r"])
            if "r" in values
            else None
        ),
        sets_count=(
            _parse_sets_count(values["s"])
            if "s" in values
            else None
        ),
    )


def _parse_weight(value: str) -> Decimal:
    """Разбирает вес с десятичной запятой или точкой."""
    weight = normalize_weight(value.replace(",", "."))
    if not _MIN_WEIGHT <= weight <= _MAX_WEIGHT:
        raise ValueError(f"Вес должен быть от {_MIN_WEIGHT} до {_MAX_WEIGHT} кг.")
    return weight


def _parse_repetitions(value: str) -> int:
    """Проверяет диапазон целого количества повторений."""
    return _parse_integer_in_range(
        value,
        label="Повторения",
        minimum=_MIN_REPETITIONS,
        maximum=_MAX_REPETITIONS,
    )


def _parse_sets_count(value: str) -> int:
    """Проверяет диапазон целого количества добавляемых подходов."""
    return _parse_integer_in_range(
        value,
        label="Количество подходов",
        minimum=_MIN_SETS_COUNT,
        maximum=_MAX_SETS_COUNT,
    )


def _parse_integer_in_range(value: str, *, label: str, minimum: int, maximum: int) -> int:
    """Проверяет, что целое значение находится в допустимом диапазоне."""
    if "." in value or "," in value:
        raise ValueError(f"{label} должны быть целым числом.")
    parsed = int(value)
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{label} должны быть от {minimum} до {maximum}.")
    return parsed


@router.inline_query(TrainingStates.set_form)
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
        return _weight_inline_results(substring)

    upper_bound = _MAX_REPETITIONS if prefix == "r" else _MAX_SETS_COUNT
    lower_bound = _MIN_REPETITIONS if prefix == "r" else _MIN_SETS_COUNT
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
        for number in range(lower_bound, upper_bound + 1)
        if substring in str(number)
    ]


def _weight_inline_results(substring: str) -> list[InlineQueryResultArticle]:
    """Строит подсказки сетки веса и вариант для корректного нестандартного веса."""
    values = [
        normalize_weight(_MIN_WEIGHT + _WEIGHT_STEP * number)
        for number in range(int((_MAX_WEIGHT - _MIN_WEIGHT) / _WEIGHT_STEP) + 1)
    ]
    normalized_query = substring.replace(",", ".")
    results = [
        _weight_inline_result(value)
        for value in values
        if normalized_query in format(value, "f")
    ]
    custom_weight = _try_parse_weight(substring)
    if custom_weight is not None and custom_weight not in values:
        results.insert(0, _weight_inline_result(custom_weight))
    return results


def _try_parse_weight(value: str) -> Decimal | None:
    """Возвращает корректный вес для inline-подсказки или None без показа ошибки."""
    try:
        return _parse_weight(value)
    except ValueError:
        return None


def _weight_inline_result(weight: Decimal) -> InlineQueryResultArticle:
    """Создаёт безопасный inline-результат выбора веса."""
    return InlineQueryResultArticle(
        id=f"w{format(weight, 'f')}",
        title=f"{format_weight(weight)} кг",
        input_message_content=InputTextMessageContent(
            message_text=f"w{format(weight, 'f')}",
            parse_mode=None,
        ),
    )


@router.message(F.text & ~F.text.startswith("/"), TrainingStates.set_form)
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
        next_step=TrainingFlowStep.SET_FORM,
    )
    if result is TrainingTransitionResult.APPLIED:
        await message.delete()


@router.callback_query(F.data == "edit_form_exercise", TrainingStates.set_form)
async def open_edit_exercises(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает из формы подхода к выбору упражнения для редактирования."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.selection.weight = None
    next_draft.selection.repetitions = None
    next_draft.selection.exercise_id = None
    next_draft.selection.exercise_name = None
    next_draft.edit.exercise_id = None
    next_draft.edit.exercise_name = None
    next_draft.edit.set_id = None
    next_draft.edit.set_number = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_SELECT_EXERCISE,
    )


@router.callback_query(F.data == "edit_form_set", TrainingStates.set_form)
async def open_edit_sets(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает из формы подхода к списку подходов выбранного упражнения."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.selection.weight = None
    next_draft.selection.repetitions = None
    next_draft.selection.exercise_id = None
    next_draft.selection.exercise_name = None
    next_draft.edit.set_id = None
    next_draft.edit.set_number = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_SELECT_SET,
    )
