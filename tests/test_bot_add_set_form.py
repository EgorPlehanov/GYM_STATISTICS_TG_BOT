"""Тесты разбора короткого ввода формы добавления подходов."""

from decimal import Decimal

import pytest

from app.bot.handlers.training_units.set_input.form import (
    _inline_results,
    parse_add_set_form_input,
)
from app.bot.keyboards.training_kb.set_input.ikb_add_set_form import (
    get_ikb_add_set_form,
)


@pytest.mark.parametrize(
    ("text", "weight", "repetitions", "sets_count"),
    [
        ("w80 r8 s3", Decimal("80.000"), 8, 3),
        ("R8w80", Decimal("80.000"), 8, None),
        ("s3", None, None, 3),
        ("w80r8s3", Decimal("80.000"), 8, 3),
        ("r8\ns2\nw80", Decimal("80.000"), 8, 2),
        ("W80,125", Decimal("80.125"), None, None),
    ],
)
def test_parse_indexed_add_set_form_input(
    text: str,
    weight: Decimal | None,
    repetitions: int | None,
    sets_count: int | None,
) -> None:
    """Индексированный ввод обновляет только явно переданные поля."""
    parsed = parse_add_set_form_input(text)

    assert parsed.weight == weight
    assert parsed.repetitions == repetitions
    assert parsed.sets_count == sets_count


@pytest.mark.parametrize(
    ("text", "weight", "repetitions", "sets_count"),
    [
        ("80×8", Decimal("80.000"), 8, None),
        ("80x8x3", Decimal("80.000"), 8, 3),
        ("80х8*3", Decimal("80.000"), 8, 3),
        ("80 / 8 / 3", Decimal("80.000"), 8, 3),
        ("80:8:3", Decimal("80.000"), 8, 3),
        ("80 8 3", Decimal("80.000"), 8, 3),
        ("80\n10\n2", Decimal("80.000"), 10, 2),
        ("80,125×8", Decimal("80.125"), 8, None),
        ("80,1256×8", Decimal("80.126"), 8, None),
    ],
)
def test_parse_positional_add_set_form_input(
    text: str,
    weight: Decimal,
    repetitions: int,
    sets_count: int | None,
) -> None:
    """Позиционный ввод поддерживает заявленные разделители и округление веса."""
    parsed = parse_add_set_form_input(text)

    assert parsed.weight == weight
    assert parsed.repetitions == repetitions
    assert parsed.sets_count == sets_count


@pytest.mark.parametrize(
    "text",
    [
        "w80 w90",
        "w80r8r9",
        "80",
        "80-8",
        "w80q8",
        "s0",
        "w500,001",
        "r1001",
        "s101",
    ],
)
def test_parse_add_set_form_input_rejects_ambiguous_or_invalid_values(text: str) -> None:
    """Повторы индекса, одиночные числа и неоднозначные разделители отвергаются."""
    with pytest.raises(ValueError):
        parse_add_set_form_input(text)


@pytest.mark.parametrize("text", ["w0", "w500", "r0", "r1000", "s1", "s100"])
def test_parse_add_set_form_input_accepts_range_boundaries(text: str) -> None:
    """Граничные значения формы принимаются включительно."""
    parse_add_set_form_input(text)


def test_weight_inline_results_accept_comma_and_dot_and_offer_custom_value() -> None:
    """Поиск веса не зависит от разделителя, а нестандартный шаг остаётся доступным."""
    comma_results = _inline_results("w", "80,5")
    dot_results = _inline_results("w", "80.5")
    custom_results = _inline_results("w", "80.125")

    assert comma_results[0].input_message_content.message_text == "w80.500"
    assert dot_results[0].input_message_content.message_text == "w80.500"
    assert custom_results[0].title == "80,125 кг"
    assert custom_results[0].input_message_content.message_text == "w80.125"


def test_weight_inline_results_do_not_offer_out_of_range_value() -> None:
    """Inline-поиск не предлагает вес за допустимой границей."""
    assert _inline_results("w", "500.001") == []


def test_add_set_form_hides_submit_until_required_fields_are_set() -> None:
    """Клавиатура не создаёт неработающую кнопку добавления до заполнения формы."""
    incomplete = get_ikb_add_set_form(
        exercise_name="Жим лежа",
        weight=None,
        repetitions=None,
        sets_count=1,
        can_submit=False,
        is_editing=False,
    )
    complete = get_ikb_add_set_form(
        exercise_name="Жим лежа",
        weight=Decimal("80.000"),
        repetitions=8,
        sets_count=1,
        can_submit=True,
        is_editing=False,
    )

    assert [button.text for button in incomplete.inline_keyboard[-1]] == ["Отменить"]
    assert [button.text for button in complete.inline_keyboard[-1]] == [
        "Отменить",
        "Добавить",
    ]


def test_edit_set_form_hides_sets_count_and_uses_save_action() -> None:
    """Редактирование одного подхода не предоставляет ввод числа подходов."""
    keyboard = get_ikb_add_set_form(
        exercise_name="Жим лежа",
        weight=Decimal("80.000"),
        repetitions=8,
        sets_count=None,
        can_submit=True,
        is_editing=True,
    )
    buttons = [button for row in keyboard.inline_keyboard for button in row]

    assert all(not button.text.startswith("Подходов") for button in buttons)
    assert any(button.callback_data == "accept_edit" for button in buttons)
    assert any(button.callback_data == "delete_set" for button in buttons)


def test_add_set_form_passes_current_values_to_inline_query() -> None:
    """Кнопки формы открывают inline-ввод с уже выбранным значением."""
    keyboard = get_ikb_add_set_form(
        exercise_name="Жим лежа",
        weight=Decimal("80.125"),
        repetitions=8,
        sets_count=3,
        can_submit=True,
        is_editing=False,
    )

    assert [
        button.switch_inline_query_current_chat
        for row in keyboard.inline_keyboard
        for button in row
        if button.switch_inline_query_current_chat is not None
    ] == ["s3", "w80,125", "r8"]


def test_add_set_form_places_sets_count_below_exercise() -> None:
    """Количество подходов располагается отдельной строкой перед весом и повторениями."""
    keyboard = get_ikb_add_set_form(
        exercise_name="Жим лежа",
        weight=Decimal("80.000"),
        repetitions=8,
        sets_count=3,
        can_submit=True,
        is_editing=False,
    )

    assert [[button.text for button in row] for row in keyboard.inline_keyboard[:3]] == [
        ["Жим лежа"],
        ["Подходов: 3"],
        ["Вес: 80 кг", "Повторы: 8"],
    ]
