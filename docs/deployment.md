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

## Public и internal API

В production API-контейнер не должен публиковать порт напрямую наружу через Docker `ports`.
Доступ из интернета должен идти только через reverse proxy.

Reverse proxy публикует:

```text
/api/*
/health
web static files
```

Reverse proxy не должен публиковать:

```text
/internal/*
```

Bot и worker обращаются к internal API по приватной Docker network:

```text
bot -> http://api:8000/internal/...
worker -> http://api:8000/internal/...
```

Все `/internal/*` endpoints дополнительно требуют service token в заголовке:

```text
X-Internal-Api-Key: <INTERNAL_API_TOKEN>
```

Этот token хранится только в backend-окружении и не передается во frontend.

Минимальный API-сервис в Docker Compose запускается командой:

```text
uv run uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

Базовая техническая проверка доступна по адресу:

```text
GET /health
```

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
- healthchecks на уровне Docker/reverse proxy;
- правила reverse proxy для запрета `/internal/*` снаружи;
- логи;
- стратегия обновления контейнеров.
