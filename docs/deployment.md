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

Версии инфраструктурных образов нужно фиксировать явно. PostgreSQL использует
`postgres:18-alpine`, а не `postgres:latest`, чтобы обновление Docker image не
поменяло major-версию базы без отдельного плана миграции.

Для PostgreSQL 18 volume монтируется в `/var/lib/postgresql`, а не в
`/var/lib/postgresql/data`. Такой layout соответствует актуальному Docker image
PostgreSQL и оставляет место для version-specific директорий данных.

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

Обычные сервисы Compose запускаются из собранного Docker image без bind mount исходников.
Это ближе к VPS-режиму и не подмешивает локальное `.venv` внутрь Linux-контейнера.

Базовая техническая проверка доступна по адресу:

```text
GET /health
```

## Миграции

Обычные сервисы `api`, `bot` и `worker` не применяют миграции при старте. Это защищает данные от неожиданных изменений при перезапуске контейнеров.

Миграции и справочники применяются явно:

```text
docker compose --profile tools run --build --rm migrate
```

`--build` нужен, чтобы сервис `migrate` использовал свежие файлы миграций и
seed-данных из текущего исходного кода. Если перед этим уже выполнялась команда
`docker compose --profile tools build`, можно запускать миграции без `--build`.

Полный сброс базы предназначен только для разработки:

```text
docker compose --profile tools run --rm db-reset
```

Команда `db-reset` должна выполняться только при `APP_ENV=dev`.

Локальный запуск с полным пересозданием окружения:

```text
docker compose down -v --remove-orphans --rmi local
docker compose pull db
docker compose --profile tools build --no-cache
docker compose up -d db
docker compose --profile tools run --rm migrate
docker compose up -d api bot
```

`docker compose --profile tools build --no-cache` пересобирает сервисы приложения:
`api`, `bot`, `migrate`, `db-reset`. PostgreSQL не собирается, потому что
использует готовый image `postgres:18-alpine`.

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

## Будущие улучшения Docker Compose

Текущий Compose-файл оставлен простым и близким к локальному запуску на VPS. По
мере перехода к production нужно отдельно вернуться к следующим улучшениям:

- задать явное `name` для Compose project, чтобы имена volume и network были
  предсказуемыми;
- рассмотреть `restart: unless-stopped` вместо `restart: always`, чтобы ручная
  остановка сервиса сохранялась после перезапуска Docker;
- добавить секцию `logging` с ограничением размера логов, чтобы они не заняли
  диск VPS;
- подготовить отдельный production Compose или override-файл;
- после добавления reverse proxy разделить Docker networks на `public` и
  `internal`;
- для масштабируемых сервисов убрать `container_name`, потому что несколько
  контейнеров не могут иметь одно и то же имя;
- рассмотреть запуск application-контейнеров не от root-пользователя;
- при появлении CI/CD перейти от локального `build` на VPS к запуску заранее
  собранных images из registry.
