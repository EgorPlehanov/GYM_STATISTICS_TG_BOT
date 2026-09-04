# 0005. Public и internal API

## Статус

Принято.

## Контекст

Проект имеет несколько клиентов:

- web frontend;
- Telegram Mini App;
- Telegram Bot;
- будущий worker.

Web frontend и Telegram Mini App работают от имени пользователя и должны использовать пользовательскую авторизацию через `httpOnly` cookie. Telegram Bot и worker работают как доверенные backend-сервисы внутри инфраструктуры проекта.

Нужно не открыть служебные endpoints наружу и при этом не продублировать бизнес-логику в разных API.

## Решение

Разделяем HTTP-входы по назначению:

```text
/api/*       публичный пользовательский API для web и Telegram Mini App
/internal/*  служебный API для bot-service и worker
```

Публичный API использует пользовательскую сессию:

```text
web / Mini App -> /api/* -> current_user -> domain -> repositories -> db
```

Internal API использует service-to-service авторизацию:

```text
bot / worker -> /internal/* -> service token -> resolve user/context -> domain -> repositories -> db
```

Routers не должны содержать бизнес-логику. Public и internal endpoints могут иметь разные DTO и разные способы авторизации, но обязаны вызывать одни и те же domain services для одинаковых пользовательских сценариев.

## Защита internal API

Для production нужно соблюдать несколько уровней защиты:

- не публиковать API-порт наружу через Docker `ports`;
- использовать Docker `expose` и приватную Docker network для связи `bot -> api`;
- не маршрутизировать `/internal/*` из интернета через reverse proxy;
- требовать service token в заголовке `X-Internal-Api-Key` для всех `/internal/*` endpoints;
- хранить service token только в backend-окружении, не передавать его во frontend.

Даже если `/internal/*` случайно станет сетево доступен, запрос без service token должен получать отказ.
Проверка service token подключается на уровне `/internal` router.

## Последствия

- Бот становится зависим от API как от центральной точки входа в backend.
- Поддержка усложняется на уровне транспорта и деплоя, потому что появляется internal auth и правила reverse proxy.
- Бизнес-логика остается единой в `app/domain`, поэтому разные интерфейсы не должны расходиться по поведению.
- Безопасность выше, чем при прямом доступе bot/worker к базе или domain-слою в обход API.
