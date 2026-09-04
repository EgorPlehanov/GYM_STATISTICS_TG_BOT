# База данных

## Назначение слоя

Слой базы данных находится в `app/db` и отвечает за:

- SQLAlchemy metadata;
- модели;
- подключение к PostgreSQL;
- фабрики sync/async-сессий;
- миграции Alembic;
- загрузку справочных данных;
- repositories для запросов.

## Структура

```text
app/db/
  base.py
  session.py
  models.py
  seed.py
  seed_data/
  repositories/

migrations/
  env.py
  script.py.mako
  versions/
```

## Пользовательская модель

Пользователь имеет внутренний primary key:

```text
user.id
```

Telegram id хранится отдельно:

```text
user.telegram_id
```

Это нужно, чтобы в будущем можно было добавить другие способы авторизации без привязки всей базы к Telegram id.

## Миграции

Структура базы управляется через Alembic.

Применение миграций:

```text
uv run alembic upgrade head
```

Создание новой миграции:

```text
uv run alembic revision --autogenerate -m "описание изменения"
```

## Справочники

Seed-данные находятся в:

```text
app/db/seed_data/
```

Загрузка справочников:

```text
uv run python -m app.db.seed
```

Seed-команда добавляет только отсутствующие записи. Проверка существования выполняется по значениям полей, кроме `id`.

## Инициализация и сброс

Обычные сервисы приложения не должны применять миграции или пересоздавать базу при старте.

Для первого запуска или релиза используется явная команда:

```text
docker compose --profile tools run --rm migrate
```

Для разработки есть отдельный полный сброс:

```text
docker compose --profile tools run --rm db-reset
```

`db-reset` удаляет схему `public`, применяет миграции и загружает справочники. Команда защищена проверкой `APP_ENV=dev` и не должна использоваться в production.

Бизнес-слой и UI-слои не должны вызывать repositories напрямую. Для сценариев приложения используется `app.domain`.
