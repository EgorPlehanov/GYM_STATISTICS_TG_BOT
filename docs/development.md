# Разработка

Документ будет уточняться по мере перехода на новую архитектуру.

## Целевой локальный запуск

Планируемые команды:

```text
docker compose up db
uvicorn app.api.main:app --reload
python -m app.bot.main
python -m app.workers.main
cd web && npm run dev
```

## Принципы разработки

- Бизнес-логика живет в `app/domain`.
- SQLAlchemy-запросы живут в `app/db/repositories`.
- Telegram-бот общается с backend через FastAPI API.
- React frontend общается с backend через FastAPI API.
- UI-слои не должны напрямую обращаться к базе данных.
- Форматы API фиксируются DTO-схемами.

## Документация

При изменении архитектуры нужно обновлять:

- `docs/architecture.md`;
- соответствующий ADR в `docs/decisions/`;
- `docs/backlog.md`, если меняется состав задач.

