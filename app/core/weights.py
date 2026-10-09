"""Единые правила хранения и отображения веса."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

WEIGHT_QUANTUM = Decimal("0.001")


def normalize_weight(value: Decimal | str | int | float) -> Decimal:
    """Приводит вес к трём десятичным знакам по правилу ROUND_HALF_UP.

    Args:
        value: исходное числовое значение веса в килограммах.

    Returns:
        Нормализованный вес в килограммах.

    Raises:
        ValueError: если значение нельзя интерпретировать как десятичное число.
    """
    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("Вес должен быть десятичным числом") from error
    return decimal_value.quantize(WEIGHT_QUANTUM, rounding=ROUND_HALF_UP)


def format_weight(value: Decimal | str | int | float) -> str:
    """Форматирует вес без незначащих нулей и с запятой как разделителем.

    Args:
        value: вес в килограммах.

    Returns:
        Компактная строка веса, например `80,125` или `80`.
    """
    normalized = normalize_weight(value)
    text = format(normalized, "f").rstrip("0").rstrip(".")
    return (text or "0").replace(".", ",")
