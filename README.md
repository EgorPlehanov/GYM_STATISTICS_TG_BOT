# GYM_STATISTICS_TG_BOT

Telegram-бот и web-приложение для учета тренировок и просмотра спортивной статистики.

Проект переводится на новую архитектуру с независимыми приложениями:

- FastAPI backend API;
- Telegram Bot;
- React/Vite web frontend;
- Telegram Mini App;
- background worker;
- PostgreSQL.

## Документация

Основная документация находится в [docs](docs/README.md).

- [Архитектура](docs/architecture.md)
- [Backlog](docs/backlog.md)
- [Разработка](docs/development.md)
- [Деплой](docs/deployment.md)
- [База данных](docs/database.md)
- [Telegram Mini App](docs/telegram-mini-app.md)
- [Архитектурные решения](docs/decisions)

## Текущий запуск

```bash
docker-compose up
```

Миграции и справочники применяются отдельной явной командой:

```bash
docker compose --profile tools run --build --rm migrate
```

Полный сброс базы для разработки:

```bash
docker compose --profile tools run --rm db-reset
```

## Лицензия

Код доступен для просмотра, но любое использование, копирование, изменение, распространение, публикация, развертывание или включение в другие проекты запрещено без предварительного письменного разрешения правообладателя.

Подробнее: [LICENSE](LICENSE).

