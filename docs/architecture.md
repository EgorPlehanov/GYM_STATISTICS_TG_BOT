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
bot -> internal FastAPI API -> domain -> repositories -> db
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
      auth/
        service.py
      users/
        schemas.py
        service.py
      groups/
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
      schemas/
        auth.py
        internal/
          users.py
          exercises.py
          trainings.py
          groups.py
      routers/
        health.py
        auth.py
        internal/
          health.py
          users.py
          exercises.py
          trainings.py
          groups.py
          ratings.py
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
      utils/

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

API делится на два типа HTTP-входов:

```text
/api/*       публичный пользовательский API для web и Telegram Mini App
/internal/*  служебный API для bot-service и worker
```

`/api/*` использует пользовательскую web-сессию. `/internal/*` должен использовать service-to-service авторизацию и не должен быть доступен из интернета.

Public и internal routes могут отличаться DTO и способом авторизации, но не должны дублировать бизнес-логику. Для одинаковых сценариев они вызывают один и тот же domain service.

Все `/internal/*` endpoints требуют заголовок:

```text
X-Internal-Api-Key: <INTERNAL_API_TOKEN>
```

Проверка подключается на уровне `/internal` router, чтобы новые служебные endpoints
не могли быть добавлены без internal auth случайно.

Технический endpoint:

```text
GET /health
```

Он используется для быстрой проверки, что API-процесс запущен и отвечает.

Служебный health endpoint:

```text
GET /internal/health
```

Он используется для проверки service-to-service авторизации внутри инфраструктуры.

Первый служебный endpoint для Telegram-бота:

```text
POST /internal/bot/users/ensure
```

Он используется обработчиком `/start`, чтобы зарегистрировать пользователя через API,
а не через прямой доступ бота к domain/db.

Служебные endpoints для Telegram admin-panel:

```text
GET /internal/bot/admin/access
GET /internal/bot/admin/status
```

Они используются ботом для проверки административного доступа и безопасного
технического статуса API. Telegram admin-panel не должна выполнять прямые SQL-запросы
и не должна показывать диагностические данные базы в чате.

Основные группы endpoint-ов:

```text
POST   /api/auth/telegram-mini-app
POST   /api/auth/telegram-login
POST   /api/auth/telegram-code/request
POST   /api/auth/telegram-code/verify
GET    /api/auth/me
POST   /api/auth/logout

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

Для web-сессий API использует `httpOnly` cookie с подписанным session token.
Клиентский JavaScript не читает токен напрямую, а отправляет cookie вместе с запросами.

### Domain

Domain layer содержит бизнес-сценарии:

- создание тренировки;
- редактирование тренировки;
- удаление тренировки;
- получение истории тренировок;
- расчет статистики;
- регистрация пользователей и Telegram-групп;
- авторизация пользователей через Telegram;
- настройка редиректа результатов в группы;
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
- вызовы internal FastAPI API.

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

## RBAC

Права доступа хранятся в базе через роли:

```text
role       справочник ролей
user_role  связь пользователя и роли
```

Базовые роли:

- `owner` - полный административный доступ;
- `admin` - административный доступ к безопасным операциям;
- `user` - обычный пользователь.

Используется подход additive roles: роли складываются и не заменяют друг друга.
Администратор остается обычным пользователем приложения, поэтому может иметь роли
`user` и `owner` одновременно. Пользовательские функции проверяют базовую роль
`user`, административные функции проверяют `admin` или `owner`.

`MAIN_ADMIN_ID` используется только как bootstrap-настройка: при создании пользователя
с этим Telegram id ему назначается роль `owner`. Дальше источником прав должна быть
база данных, а не переменная окружения.

Для Telegram-бота фильтр администратора проверяет роль через internal API. Аварийный
fallback на `MAIN_ADMIN_ID` допустим только для восстановления доступа, если backend API
временно недоступен.

## Даты тренировок

`Training.date` хранит календарную дату тренировки без времени.

Это осознанное разделение смыслов:

- `Training.date` - день тренировки;
- `Set.execution_time` - точное время выполнения подхода, если оно фиксировалось;
- `created_at` и `updated_at` - технические даты создания и обновления записи.

В API и FSM Telegram-бота дата тренировки передается в формате `YYYY-MM-DD`.
Время подходов остается `datetime`.

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
