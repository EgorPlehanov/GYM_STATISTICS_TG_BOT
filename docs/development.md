# Разработка

Документ будет уточняться по мере перехода на новую архитектуру.

## Целевой локальный запуск

Планируемые команды:

```text
uv sync
docker compose up db
uv run uvicorn app.api.main:app --reload
uv run python -m app.bot.main
uv run python -m app.workers.main
cd web && npm run dev
```

Планируемая подготовка базы:

```text
uv run alembic upgrade head
uv run python -m app.db.seed
```

Через Docker Compose:

```text
docker compose up api
docker compose --profile tools run --rm migrate
docker compose --profile tools run --rm db-reset
```

`db-reset` полностью пересоздает схему БД и разрешен только при `APP_ENV=dev`.

## Зависимости

Python-зависимости управляются через `uv`.

Текущая backend-часть проекта зафиксирована на Python 3.10:

```text
requires-python = ">=3.10,<3.11"
```

Ограничение связано с совместимостью текущих версий `aiogram` и `aiogram3-calendar`.

Источник прямых зависимостей:

```text
pyproject.toml
```

Lock-файл:

```text
uv.lock
```

Базовые команды:

```text
uv sync
uv add package-name
uv add --dev package-name
uv run pytest
uv run ruff check .
```

Если в текущей Windows-сессии команда `uv` еще не подхватилась в `PATH`, можно использовать форму:

```text
python -m uv sync
python -m uv run pytest
```

`requirements.txt` больше не используется как источник зависимостей.

## Конфигурация

Единая точка конфигурации:

```text
app/core/config.py
```

Старый модуль `config_reader.py` временно оставлен как совместимая обертка для существующего кода.

Пример переменных окружения находится в `.env.example`.

Обязательные группы настроек:

- приложение и окружение;
- Telegram Bot;
- PostgreSQL;
- Backend API;
- Web frontend;
- sessions and cookies.

## Принципы разработки

- Бизнес-логика живет в `app/domain`.
- SQLAlchemy-запросы живут в `app/db/repositories`.
- FastAPI-приложение создается в `app/api/main.py`.
- API routes живут в `app/api/routers`.
- Зависимости HTTP-запросов живут в `app/api/deps.py`.
- Telegram-бот общается с backend через FastAPI API.
- React frontend общается с backend через FastAPI API.
- UI-слои не должны напрямую обращаться к базе данных.
- Форматы API фиксируются DTO-схемами.

## Документация

При изменении архитектуры нужно обновлять:

- `docs/architecture.md`;
- соответствующий ADR в `docs/decisions/`;
- `docs/backlog.md`, если меняется состав задач.
