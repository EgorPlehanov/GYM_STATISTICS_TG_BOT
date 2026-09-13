"""Проверки архитектурных границ импортов между слоями проекта."""

import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "app"


@dataclass(frozen=True)
class ImportBoundaryRule:
    """Правило, запрещающее одному слою импортировать другой слой.

    Attributes:
        source: каталог или файл, в котором проверяются импорты.
        forbidden_imports: запрещенные префиксы импортируемых модулей.
        description: человекочитаемое описание нарушения.
    """

    source: Path
    forbidden_imports: tuple[str, ...]
    description: str


RULES = (
    ImportBoundaryRule(
        source=APP_ROOT / "bot",
        forbidden_imports=("app.db", "app.domain"),
        description="bot layer должен обращаться к backend только через internal API",
    ),
    ImportBoundaryRule(
        source=APP_ROOT / "domain",
        forbidden_imports=("app.api", "app.bot", "fastapi", "aiogram"),
        description="domain layer не должен зависеть от HTTP или Telegram UI",
    ),
    ImportBoundaryRule(
        source=APP_ROOT / "db" / "repositories",
        forbidden_imports=("app.api.schemas", "pydantic"),
        description="repositories не должны зависеть от API DTO",
    ),
    ImportBoundaryRule(
        source=APP_ROOT / "db" / "models.py",
        forbidden_imports=("app.domain", "app.api", "app.bot"),
        description="db models должны оставаться нижним слоем без зависимостей на app-слои выше",
    ),
)


def test_architecture_import_boundaries() -> None:
    """Проверяет, что слои проекта не импортируют запрещенные зависимости."""
    violations: list[str] = []

    for rule in RULES:
        for file_path in _iter_python_files(rule.source):
            for imported_module, line_number in _iter_imports(file_path):
                if _is_forbidden_import(imported_module, rule.forbidden_imports):
                    relative_path = file_path.relative_to(PROJECT_ROOT)
                    violations.append(
                        f"{relative_path}:{line_number}: {imported_module} - {rule.description}"
                    )

    assert violations == []


def _iter_python_files(source: Path) -> Iterable[Path]:
    """Возвращает Python-файлы из проверяемого источника.

    Args:
        source: путь к файлу или каталогу.

    Returns:
        Итератор Python-файлов. Для несуществующего пути возвращается пустой
        итератор, чтобы правило можно было добавить до появления слоя в коде.
    """
    if not source.exists():
        return ()

    if source.is_file():
        return (source,) if source.suffix == ".py" else ()

    return source.rglob("*.py")


def _iter_imports(file_path: Path) -> Iterable[tuple[str, int]]:
    """Извлекает импортируемые модули из Python-файла.

    Args:
        file_path: путь к Python-файлу.

    Returns:
        Пары из имени импортируемого модуля и номера строки.
    """
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                yield node.module, node.lineno


def _is_forbidden_import(module: str, forbidden_imports: tuple[str, ...]) -> bool:
    """Проверяет, относится ли импорт к запрещенному префиксу."""
    return any(
        module == forbidden_import or module.startswith(f"{forbidden_import}.")
        for forbidden_import in forbidden_imports
    )
