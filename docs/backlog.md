# Backlog

Backlog фиксирует крупные задачи перехода на новую архитектуру и важные аспекты, которые нельзя потерять в процессе.

Статусы:

- `[ ]` не начато
- `[~]` в работе
- `[x]` готово

## 1. Архитектура и документация

- [x] Зафиксировать целевую архитектуру в документации.
- [x] Зафиксировать ключевые архитектурные решения в ADR.
- [ ] Описать правила импортов между слоями.
- [ ] Описать lifecycle запроса от web/bot до базы.
- [x] Обновить корневой README после создания новой структуры.

## 2. Структура проекта

- [x] Создать каталог `app/`.
- [x] Создать каталог `web/`.
- [x] Создать каталог `docker/`.
- [x] Создать каталог `tests/`.
- [x] Создать каталог `migrations/`.
- [ ] Перенести старые Telegram-модули в `app/bot/`.
- [ ] Перенести текущие `utils` по назначению: bot formatters, domain helpers, shared utils.

## 3. Backend Core

- [x] Перенести конфигурацию в `app/core/config.py`.
- [x] Добавить настройки окружений `dev`, `test`, `prod`.
- [x] Перейти с `requirements.txt` на `pyproject.toml` и `uv`.
- [x] Сгенерировать `uv.lock`.
- [ ] Добавить централизованное логирование.
- [ ] Добавить базовые project exceptions.
- [ ] Добавить security helpers для cookies, tokens и Telegram validation.
- [x] Создать `.env.example`.

## 4. Database

- [x] Перенести SQLAlchemy session setup в `app/db/session.py`.
- [x] Перенести модели в `app/db/models.py`.
- [x] Изменить модель пользователя: внутренний `id` плюс уникальный `telegram_id`.
- [x] Настроить Alembic.
- [x] Создать начальную миграцию.
- [x] Перенести seed JSON в `app/db/seed_data/`.
- [x] Реализовать seed-команду для справочников.
- [x] Убрать production-зависимость от `Base.metadata.create_all()`.

## 5. Repositories

- [x] Создать `app/db/repositories/users.py`.
- [x] Создать `app/db/repositories/groups.py`.
- [x] Создать `app/db/repositories/exercises.py`.
- [x] Создать `app/db/repositories/trainings.py`.
- [x] Создать `app/db/repositories/ratings.py`.
- [x] Создать `app/db/repositories/export.py`.
- [ ] Перенести SQL-запросы из старого `db/queries`.
- [ ] Убрать Telegram/UI-логику из слоя работы с данными.

## 6. Domain Services

- [x] Создать `UsersService`.
- [x] Создать `ExercisesService`.
- [x] Создать `TrainingsService`.
- [x] Создать `StatisticsService`.
- [x] Создать `RatingsService`.
- [x] Создать `ExportService`.
- [ ] Перенести сценарии создания, обновления и удаления тренировок.
- [ ] Перенести сценарии получения статистики.
- [ ] Подготовить постановку задач на пересчет рейтинга через worker.

## 7. FastAPI API

- [x] Создать `app/api/main.py`.
- [x] Создать dependency layer в `app/api/deps.py`.
- [x] Создать router `auth`.
- [x] Создать router `users`.
- [x] Создать router `exercises`.
- [x] Создать router `trainings`.
- [x] Создать router `statistics`.
- [x] Создать router `export`.
- [ ] Настроить CORS для web frontend.
- [ ] Настроить OpenAPI metadata.
- [ ] Описать базовый API contract.

## 8. Авторизация

- [ ] Реализовать Telegram Mini App `initData` validation.
- [ ] Реализовать Telegram Login Widget validation.
- [ ] Реализовать одноразовый код через бота.
- [ ] Реализовать безопасную web-сессию через `httpOnly` cookie.
- [ ] Добавить logout.
- [ ] Добавить `GET /api/me`.
- [ ] Добавить тесты на validation Telegram auth.

## 9. Telegram Bot

- [ ] Перенести entrypoint в `app/bot/main.py`.
- [x] Создать API client для бота.
- [ ] Перенести handlers.
- [ ] Перенести keyboards.
- [ ] Перенести middlewares.
- [ ] Перенести filters.
- [ ] Перенести FSM states.
- [ ] Перевести основные сценарии бота на вызовы FastAPI API.
- [ ] Добавить сценарий генерации одноразового кода для web login.

## 10. Worker

- [ ] Выбрать механизм фоновых задач.
- [x] Создать `app/workers/main.py`.
- [ ] Реализовать задачу пересчета рейтинга пользователя.
- [ ] Вызывать постановку задачи после create/update/delete training.
- [ ] Описать retry/error handling.
- [ ] Добавить отдельный сервис worker в Docker Compose.

## 11. Web Frontend

- [ ] Создать React/Vite/TypeScript проект в `web/`.
- [ ] Настроить router.
- [ ] Настроить API client.
- [ ] Настроить session handling.
- [ ] Добавить Telegram Mini App adapter.
- [ ] Добавить mobile-first layout.
- [ ] Реализовать экран входа.
- [ ] Реализовать dashboard статистики.
- [ ] Реализовать список тренировок.
- [ ] Реализовать создание и редактирование тренировки.
- [ ] Реализовать просмотр прогресса по упражнению.

## 12. Telegram Mini App

- [ ] Добавить определение Telegram Mini App режима.
- [ ] Передавать `initData` на backend.
- [ ] Поддержать Telegram theme params.
- [ ] Поддержать Telegram BackButton.
- [ ] Продумать MainButton для ключевых действий.
- [ ] Проверить поведение viewport на мобильных устройствах.
- [ ] Подготовить инструкцию настройки Mini App в BotFather.

## 13. Export

- [ ] Оставить текущий export как есть на время архитектурного перехода.
- [ ] Отдельно спроектировать web export.
- [ ] Решить форматы: CSV, XLSX, JSON.
- [ ] Добавить отдельную документацию по export после проектирования.

## 14. Docker и деплой

- [ ] Подготовить Dockerfile для backend/bot/worker.
- [ ] Подготовить Dockerfile для web.
- [ ] Обновить `docker-compose.yml`.
- [ ] Добавить сервис `api`.
- [ ] Добавить сервис `bot`.
- [ ] Добавить сервис `worker`.
- [ ] Добавить сервис `web`.
- [ ] Добавить reverse proxy.
- [ ] Добавить production env documentation.
- [ ] Описать backup PostgreSQL.

## 15. Тесты

- [ ] Добавить тесты domain services.
- [ ] Добавить тесты repositories.
- [ ] Добавить тесты API.
- [ ] Добавить тесты auth.
- [ ] Добавить тесты worker-задач.
- [ ] Добавить smoke-тест запуска backend.
- [ ] Добавить smoke-тест web build.

## Отложенные решения

- [ ] Решить, нужно ли менять `Training.date` с `datetime` на отдельный `date`.
- [ ] Подробно спроектировать export.
- [ ] Выбрать Caddy или Nginx для VPS.
- [ ] Выбрать механизм фоновых задач: простой async worker, task queue, Redis/RQ, Celery, Dramatiq или другой вариант.
- [ ] Решить, нужен ли отдельный API token для bot-service при обращении к backend.
