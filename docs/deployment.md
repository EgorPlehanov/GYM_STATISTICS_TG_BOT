# Деплой

Целевой деплой проекта: VPS под полным контролем.

## Планируемые сервисы

```text
postgres
api
bot
worker
web
reverse-proxy
```

## Базовая схема

```text
Internet
  ↓
Reverse Proxy
  ↓
web static files
api service
```

Telegram Bot работает отдельным процессом и обращается к `api service`.

## Миграции

Обычные сервисы `api`, `bot` и `worker` не применяют миграции при старте. Это защищает данные от неожиданных изменений при перезапуске контейнеров.

Миграции и справочники применяются явно:

```text
docker compose --profile tools run --rm migrate
```

Полный сброс базы предназначен только для разработки:

```text
docker compose --profile tools run --rm db-reset
```

Команда `db-reset` должна выполняться только при `APP_ENV=dev`.

## Что нужно будет описать перед production

- домены и TLS;
- переменные окружения;
- миграции при релизе;
- backup PostgreSQL;
- restart policy;
- healthchecks;
- логи;
- стратегия обновления контейнеров.
