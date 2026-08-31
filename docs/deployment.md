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

## Что нужно будет описать перед production

- домены и TLS;
- переменные окружения;
- миграции при релизе;
- backup PostgreSQL;
- restart policy;
- healthchecks;
- логи;
- стратегия обновления контейнеров.

