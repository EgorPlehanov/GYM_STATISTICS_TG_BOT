# Backlog

Backlog фиксирует крупные задачи перехода на новую архитектуру и важные аспекты, которые нельзя потерять в процессе.

Статусы:

- `[ ]` не начато
- `[~]` в работе
- `[x]` готово

## 1. Архитектура и документация

- [x] Зафиксировать целевую архитектуру в документации.
- [x] Зафиксировать ключевые архитектурные решения в ADR.
- [x] Описать правила public/internal API.
- [x] Разделить internal API router по доменным зонам.
- [x] Разделить DTO-схемы internal API по доменным зонам.
- [ ] Описать правила импортов между слоями.
- [ ] Описать lifecycle запроса от web/bot до базы.
- [x] Зафиксировать целевую архитектуру Telegram-бота.
- [x] Обновить корневой README после создания новой структуры.

## 2. Структура проекта

- [x] Создать каталог `app/`.
- [x] Создать каталог `web/`.
- [x] Создать каталог `docker/`.
- [x] Создать каталог `tests/`.
- [x] Создать каталог `migrations/`.
- [x] Перенести старые Telegram-модули в `app/bot/`.
- [x] Удалить старый каталог `db/` после переноса в `app/db`.
- [~] Перенести текущие `utils` по назначению: bot formatters, domain helpers, shared utils.

## 3. Backend Core

- [x] Перенести конфигурацию в `app/core/config.py`.
- [x] Добавить настройки окружений `dev`, `test`, `prod`.
- [x] Перейти с `requirements.txt` на `pyproject.toml` и `uv`.
- [x] Сгенерировать `uv.lock`.
- [ ] Добавить централизованное логирование.
- [ ] Добавить базовые project exceptions.
- [x] Добавить security helpers для cookies, tokens и Telegram validation.
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
- [x] Убрать автоматические миграции и seed из старта обычных контейнеров.
- [x] Добавить явный `migrate`-сервис.
- [x] Добавить dev-only `db-reset`-команду.

## 5. Repositories

- [x] Создать `app/db/repositories/users.py`.
- [x] Создать `app/db/repositories/groups.py`.
- [x] Создать `app/db/repositories/exercises.py`.
- [x] Создать `app/db/repositories/trainings.py`.
- [x] Создать `app/db/repositories/ratings.py`.
- [x] Создать `app/db/repositories/export.py`.
- [x] Перенести SQL-запросы из старого `db/queries`.
- [x] Убрать Telegram/UI-логику из слоя работы с данными.
- [ ] Типизировать сложные результаты repositories через dataclass/TypedDict/domain result objects без привязки к Pydantic API-схемам.
- [ ] Переработать `update_or_create_user_exercise_rating`: разделить расчет кандидатов рейтинга и сохранение, заменить per-row select/update/create на PostgreSQL upsert и сохранить читаемость сложного SQL/ORM-запроса.

## 6. Domain Services

- [x] Создать `UsersService`.
- [x] Создать `GroupsService`.
- [x] Создать `ExercisesService`.
- [x] Создать `TrainingsService`.
- [x] Создать `StatisticsService`.
- [x] Создать `RatingsService`.
- [x] Создать `ExportService`.
- [x] Перенести сценарии создания, обновления и удаления тренировок.
- [x] Перенести сценарии получения статистики.
- [ ] Подготовить постановку задач на пересчет рейтинга через worker.

## 7. FastAPI API

- [x] Создать `app/api/main.py`.
- [x] Создать dependency layer в `app/api/deps.py`.
- [x] Добавить health endpoint `GET /health`.
- [x] Создать router `auth`.
- [x] Создать router `users`.
- [x] Создать router `exercises`.
- [x] Создать router `trainings`.
- [x] Создать router `statistics`.
- [x] Создать router `export`.
- [x] Настроить базовый CORS для web frontend.
- [x] Настроить базовую OpenAPI metadata.
- [ ] Описать базовый API contract.
- [x] Создать `/internal/*` router group для bot-service и worker.
- [x] Добавить service-to-service auth для `/internal/*`.
- [x] Добавить internal endpoints для минимальной Telegram admin-panel.

## 8. Авторизация

- [x] Реализовать Telegram Mini App `initData` validation.
- [x] Реализовать Telegram Login Widget validation.
- [ ] Реализовать одноразовый код через бота после введения Redis.
- [x] Реализовать безопасную web-сессию через `httpOnly` cookie.
- [x] Добавить logout.
- [x] Добавить `GET /api/auth/me`.
- [x] Добавить тесты на validation Telegram auth.
- [x] Добавить базовые RBAC-таблицы `role` и `user_role`.
- [x] Добавить seed базовых ролей `owner`, `admin`, `user`.
- [x] Назначать `owner` через bootstrap-настройку `MAIN_ADMIN_ID`.
- [ ] Перейти на server-side sessions через таблицу сессий или Redis.
- [ ] Использовать случайный `sid` в cookie/session token вместо пользовательских идентификаторов.
- [ ] Реализовать управление ролями через admin API и web admin-panel.
- [ ] Добавить модель пользовательских согласий: факт, дата, версия, источник, отзыв и правила удаления/обезличивания данных.
- [ ] Расширить проверку доступа пользователя до `ensure_user_access`: создание пользователя, проверка согласия и ограничение сценариев без активного согласия.

## 9. Telegram Bot

- [x] Перенести entrypoint в `app/bot/main.py`.
- [x] Создать API client для бота.
- [x] Перенести handlers.
- [x] Перенести keyboards.
- [x] Перенести middlewares.
- [x] Перенести filters.
- [x] Перенести FSM states.
- [x] Перевести `/start` на вызов `/internal/bot/users/ensure`.
- [x] Добавить единый helper создания пользователя на входе в основные сценарии бота.
- [x] Перевести старт сценария `/training` на `/internal/bot/trainings/start-context`.
- [x] Перевести выбор упражнений в боте на вызовы `/internal/bot/exercises`.
- [x] Перевести выбор даты и загрузку тренировки в боте на вызовы `/internal/bot/trainings`.
- [x] Перевести сохранение и удаление тренировки при смене даты в боте на `/internal/bot/trainings`.
- [x] Перевести DB-операции редиректа результата тренировки в группы на `/internal/*`.
- [x] Перевести запуск пересчета рейтинга после сохранения тренировки на `/internal/*`.
- [x] Перевести команду `/statistics` на `/internal/bot/statistics/exercise-rating`.
- [x] Перевести команду `/export_data` на `/internal/bot/export/data`.
- [x] Перевести команду `/redirect` на `/internal/bot/groups/redirect-settings`.
- [x] Перевести события состояния бота в группах и личных чатах на `/internal/*`.
- [x] Перевести события участников групп на `/internal/*`.
- [x] Заменить старую Telegram admin-panel на минимальную панель `/admincmd` и `/admin_status`.
- [x] Удалить admin photo handler.
- [x] Удалить старую команду `/db_monitoring` с прямым доступом к БД.
- [~] Перевести основные сценарии бота на вызовы `/internal/*`.
- [ ] Добавить сценарий генерации одноразового кода для web login.
- [ ] Описать JSON-friendly формат FSM training draft для Telegram-бота.
- [ ] Заменить временный `training_data: dict[str, Any]` в internal training API на строгие DTO.
- [ ] Добавить adapter `API DTO -> FSM draft -> API DTO` для сценариев тренировки.
- [x] Вынести проверку открытого HTTP-клиента в `BotApiClient` в приватный helper вместо повторения проверки в каждом методе.
- [x] Вынести базовый HTTP-контекст и методы `users/admin` из `app/bot/client.py` в пакет `app/bot/api_client/`.
- [x] Перенести DTO `app/bot/api_client` в отдельный пакет `app/bot/api_client/schemas/`.
- [x] Вынести методы и DTO `exercises` из `app/bot/client.py` в пакет `app/bot/api_client/`.
- [x] Вынести методы и DTO `statistics/export` из `app/bot/client.py` в пакет `app/bot/api_client/`.
- [x] Вынести методы и DTO `groups` из `app/bot/client.py` в пакет `app/bot/api_client/`.
- [ ] Решить, нужен ли отдельный пакет `app/bot/api_client/mappers/`, если преобразований API payload -> DTO станет больше одного простого случая.
- [x] Вынести методы и DTO `trainings` из `app/bot/client.py` в пакет `app/bot/api_client/`.
- [x] Разделить `app/bot/client.py` на пакет `app/bot/api_client/` по доменным зонам после завершения переноса основных сценариев на internal API.
- [x] Убрать реэкспорт DTO из `app/bot/client.py` и перевести handlers/utils на прямые импорты из `app/bot/api_client/schemas/`.
- [ ] Убрать переходную поддержку `datetime` для `Training.date` после перевода FSM/API на строгие `date`-контракты.
- [x] Удалить устаревший `DBSessionMiddleware` из `app/bot/middlewares`, так как бот больше не должен обращаться к БД напрямую.
- [x] Удалить или перенести неиспользуемый `app/bot/utils/get_chat_members.py` после проверки, что сценарии синхронизации участников групп больше на него не опираются.
- [x] Убрать debug-выводы `print()` из обработчиков бота и заменить их логированием после появления централизованного logging.
- [x] Почистить `app/bot/handlers/error.py`: удалить старые закомментированные заготовки, убрать дубли импортов, вынести форматирование admin-уведомления в отдельную функцию.
- [x] Заменить wildcard imports в `app/bot/keyboards/*/__init__.py` и `app/bot/handlers/redirect_units/__init__.py` на явные импорты и `__all__`.
- [x] Исправить старые опечатки в Python-именах файлов, функций и переменных: `acept` -> `accept`, `atribute` -> `attribute`, `formate` -> `format`.
- [ ] Исправить legacy callback/state/FSM data values `acept_*` после перевода сценария тренировки на строгий FSM draft.
- [x] Выделить `TrainingStates`, `TrainingMode` и связанные кнопочные настройки из `app/bot/training_types.py` в feature-пакет тренировки.
- [x] Разделить `app/bot/handlers/training_units` по устойчивым зонам сценария: выбор даты, выбор упражнения, ввод подхода, редактирование, завершение тренировки.
- [x] Разделить `app/bot/keyboards/training_kb` по устойчивым зонам сценария: меню, дата, упражнение, ввод подхода, редактирование, завершение.
- [x] Вынести операции изменения FSM-структуры тренировки из `app/bot/utils/edit_exercise_data.py` в модуль draft/use-case helpers внутри feature-пакета тренировки.
- [x] Вынести training-specific helpers `check_accept_addition` и `weight_repetitions_modes` из `app/bot/utils` в FSM-пакет тренировки.
- [x] Перенести форматирование тренировок и рейтингов из `app/bot/utils` в `app/bot/formatters`.
- [x] Перенести простой bot export presentation helper из `app/bot/utils` в `app/bot/formatters/export.py`.
- [x] Перенести отправку результата тренировки в группы из `app/bot/utils` в training flow и исправить параметры helper-а.
- [x] Перенести разбиение Telegram-сообщений из `app/bot/utils` в `app/bot/formatters/messages.py`.
- [x] Удалить неиспользуемый helper `app/bot/utils/number_to_emojis.py`.
- [ ] Пересмотреть inline payload выбора упражнения: убрать runtime-only `Fernet.generate_key()` и заменить на устойчивый signed/Redis-backed payload.
- [x] Описать правила структуры `app/bot`: где живут handlers, keyboards, formatters, filters, middlewares, FSM draft и API client.
- [ ] Перевести aiogram FSM storage с `MemoryStorage` на Redis после выбора Redis как инфраструктурного сервиса.
- [ ] Заменить `app/bot/utils/migration_cache.py` на Redis TTL key для обработки миграции Telegram group -> supergroup.
- [ ] Отвязать локальный календарь `app/bot/keyboards/training_kb/date` от внешней зависимости `aiogram3-calendar`.
- [ ] Спроектировать расширенную Telegram admin-panel после появления реальных административных сценариев.

## 10. Worker

- [ ] Выбрать механизм фоновых задач.
- [x] Создать `app/workers/main.py`.
- [ ] Реализовать задачу пересчета рейтинга пользователя.
- [ ] Заменить синхронный internal endpoint пересчета рейтинга на постановку worker-задачи.
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
- [x] Передавать `initData` на backend.
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
- [ ] Спроектировать общий модуль `app/export/excel` для сложной генерации Excel-файлов, если export понадобится bot и web frontend.
- [ ] Для тяжелой генерации export-файлов использовать worker-задачу вместо выполнения внутри API request или Telegram handler.

## 14. Docker и деплой

- [x] Подготовить Dockerfile для backend/bot.
- [ ] Подготовить Dockerfile для web.
- [x] Обновить `docker-compose.yml`.
- [x] Добавить сервис `api`.
- [x] Добавить сервис `bot`.
- [ ] Добавить сервис `worker`.
- [ ] Добавить сервис `web`.
- [x] Добавить `.dockerignore`.
- [x] Зафиксировать major-версию PostgreSQL Docker image.
- [ ] Добавить reverse proxy.
- [ ] Запретить внешний доступ к `/internal/*` на уровне reverse proxy.
- [ ] В production заменить публикацию API-порта через `ports` на внутренний `expose`.
- [ ] Добавить production env documentation.
- [ ] Описать backup PostgreSQL.
- [ ] Задать явное `name` для Docker Compose project, чтобы volume/network имели стабильные имена.
- [ ] Рассмотреть замену `restart: always` на `restart: unless-stopped` для production.
- [ ] Добавить ограничение размера Docker-логов через секцию `logging`.
- [ ] Подготовить отдельный production Compose или override-файл.
- [ ] После появления reverse proxy разделить Docker networks на public/internal.
- [ ] Убрать `container_name` у масштабируемых сервисов, если понадобится запуск нескольких экземпляров.
- [ ] Рассмотреть запуск application-контейнеров не от root-пользователя.
- [ ] Перейти на готовые application images из registry, если появится CI/CD сборка.

## 15. Тесты

- [ ] Добавить тесты domain services.
- [ ] Добавить тесты repositories.
- [ ] Добавить тесты API.
- [x] Добавить тесты auth.
- [ ] Добавить тесты сериализации и восстановления FSM training draft.
- [ ] Добавить тесты операций над draft тренировки: добавить упражнение, добавить подход, изменить подход, удалить подход, удалить упражнение.
- [ ] Добавить тесты bot formatters для текста тренировки, рейтинга и export-представления.
- [ ] Добавить тесты устойчивости inline payload выбора упражнения после рестарта процесса или смены контейнера.
- [ ] Добавить repository/domain тесты пересчета рейтинга: дефолтные ранги, exercise-specific ранги, обновление существующего рейтинга и создание нового рейтинга через upsert.
- [ ] Добавить тесты worker-задач.
- [x] Добавить smoke-тест запуска backend.
- [ ] Добавить smoke-тест web build.

## Отложенные решения

- [x] Решить, нужно ли менять `Training.date` с `datetime` на отдельный `date`.
- [ ] Подробно спроектировать export.
- [ ] Выбрать Caddy или Nginx для VPS.
- [ ] Выбрать механизм фоновых задач: простой async worker, task queue, Redis/RQ, Celery, Dramatiq или другой вариант.
- [ ] Ввести Redis для временных данных: одноразовые auth-коды, будущие `sid`-сессии, aiogram FSM storage и короткие TTL-флаги бота.
- [ ] Решить, хранить ли inline payload бота через Redis TTL или через подписанный payload с постоянным секретом.
- [ ] Решить, нужно ли выделять отдельные feature-пакеты внутри `app/bot` для training, redirect, admin и export.
- [ ] После удаления `aiogram3-calendar` пересмотреть ограничение Python `>=3.10,<3.11`.
- [x] Решить, нужен ли отдельный API token для bot-service при обращении к backend.
