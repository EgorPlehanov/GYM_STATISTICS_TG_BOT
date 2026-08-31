# Архитектура проекта

## Цель

Проект развивается из Telegram-бота для учета тренировок в систему с несколькими независимыми интерфейсами:

- Telegram Bot.
- Web SPA.
- Telegram Web App / Mini App.

Все интерфейсы должны использовать единый backend API, чтобы бизнес-логика, права доступа, авторизация, статистика и работа с данными не дублировались.

## Целевая схема

```text
Telegram Bot ─────┐
                  │
React/Vite Web ───┼── FastAPI API ── Domain Services ── Repositories ── PostgreSQL
                  │
Telegram Mini App ┘

Worker ─────────────── FastAPI/domain/db для фоновых задач
```

## Главный принцип

Backend API является центральной точкой доступа к функциональности.

Telegram-бот не должен напрямую обращаться к базе или доменному слою. Он должен работать как API-клиент:

```text
bot -> FastAPI API -> domain -> repositories -> db
```

Веб-версия и Telegram Mini App работают по той же схеме:

```text
web -> FastAPI API -> domain -> repositories -> db
```

Такой подход дает единый контракт и избавляет от будущей переделки, когда функциональности станет больше.

## Целевая структура каталогов

```text
GYM_STATISTICS_TG_BOT/
  app/
    core/
      config.py
      logging.py
      security.py
      exceptions.py

    db/
      base.py
      session.py
      models.py
      seed.py
      seed_data/
      repositories/
        users.py
        groups.py
        exercises.py
        trainings.py
        ratings.py
        export.py

    domain/
      users/
        schemas.py
        service.py
      exercises/
        schemas.py
        service.py
      trainings/
        schemas.py
        service.py
      statistics/
        schemas.py
        service.py
      ratings/
        service.py
      export/
        service.py

    api/
      main.py
      deps.py
      routers/
        auth.py
        users.py
        exercises.py
        trainings.py
        statistics.py
        export.py

    bot/
      main.py
      client.py
      handlers/
      keyboards/
      middlewares/
      filters/
      states/
      formatters/

    workers/
      main.py
      tasks/

  web/
    src/
      app/
      pages/
      widgets/
      features/
      entities/
      shared/
    public/
    package.json
    vite.config.ts
    tsconfig.json

  migrations/
  docs/
  tests/
  docker/
  docker-compose.yml
  Dockerfile
  README.md
  .env.example
  pyproject.toml
```

## Слои

### API

FastAPI предоставляет внешний контракт для всех клиентов.

Основные группы endpoint-ов:

```text
POST   /api/auth/telegram-mini-app
POST   /api/auth/telegram-login
POST   /api/auth/telegram-code/request
POST   /api/auth/telegram-code/verify
GET    /api/me

GET    /api/exercises
GET    /api/trainings
POST   /api/trainings
GET    /api/trainings/{training_id}
PUT    /api/trainings/{training_id}
DELETE /api/trainings/{training_id}

GET    /api/statistics/summary
GET    /api/statistics/exercises
GET    /api/export
```

DTO-схемы для API будут добавляться при реализации frontend и backend-контрактов.

### Domain

Domain layer содержит бизнес-сценарии:

- создание тренировки;
- редактирование тренировки;
- удаление тренировки;
- получение истории тренировок;
- расчет статистики;
- постановка задач на пересчет рейтинга;
- подготовка данных для экспорта.

Domain не должен знать про Telegram, React, HTTP, HTML или конкретный UI.

### Repositories

Repositories инкапсулируют работу с базой данных.

Они отвечают за:

- SQLAlchemy-запросы;
- выборки;
- вставки;
- обновления;
- удаления;
- транзакции на уровне данных, если они не относятся к бизнес-сценарию.

Repositories не должны форматировать сообщения для Telegram или ответы для frontend.

### Bot

Telegram Bot является API-клиентом.

Он отвечает за:

- команды;
- состояния aiogram FSM;
- Telegram-кнопки;
- форматирование сообщений;
- вызовы FastAPI API.

Бот не должен содержать основную бизнес-логику.

### Web

Web является React/Vite SPA.

Оно должно работать в двух режимах:

- обычный браузер;
- Telegram Mini App.

Frontend проектируется mobile-first, потому что Telegram Mini App чаще всего будет открываться на телефоне.

### Worker

Worker используется для фоновых задач:

- пересчет рейтингов;
- тяжелая статистика;
- экспорт данных;
- будущие уведомления и периодические задачи.

На старте worker нужен прежде всего для пересчета рейтинга после изменений тренировок.

## Данные и идентичность пользователя

Основная пользовательская сущность должна иметь внутренний первичный ключ.

Telegram id хранится отдельно:

```text
id           внутренний primary key
telegram_id  уникальный Telegram user id
```

Такой подход оставляет возможность добавить другие способы авторизации в будущем.

## Даты тренировок

На первом этапе логика дат остается близкой к текущей реализации.

Отдельное решение по переходу с `datetime` на `date` для тренировочного дня будет принято позже.

## Миграции и seed-данные

Структура базы управляется через Alembic.

Справочники упражнений, рангов и порогов рейтинга загружаются отдельной seed-командой:

```text
python -m app.db.seed
```

## Деплой

Целевой деплой: VPS под полным контролем проекта.

Основные сервисы:

```text
postgres
api
bot
web
worker
reverse-proxy
```

В роли reverse proxy можно использовать Caddy или Nginx. Конкретный выбор будет зафиксирован отдельным решением перед настройкой production-деплоя.

