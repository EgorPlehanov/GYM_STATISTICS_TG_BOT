# 0002. Стратегия авторизации

## Статус

Принято.

## Контекст

Web frontend должен работать как обычный сайт и как Telegram Mini App. В будущем возможны другие способы авторизации, поэтому модель пользователя не должна быть жестко привязана к Telegram id как primary key.

## Решение

Используем внутренний primary key пользователя:

```text
id
```

Telegram id храним отдельно:

```text
telegram_id
```

Поддерживаем способы входа:

- Telegram Mini App `initData`;
- Telegram Login Widget;
- одноразовый код через Telegram-бота.

Для web-сессий используем безопасный вариант с `httpOnly` cookie.

На первом этапе API реализует:

- проверку Telegram Login Widget по HMAC-SHA-256;
- создание или обновление пользователя по Telegram id;
- stateless web-сессию через подписанный JWT в `httpOnly` cookie;
- endpoint `GET /api/auth/me`;
- endpoint `POST /api/auth/logout`.

JWT не должен хранить Telegram id. В текущей реализации payload содержит только внутренний `sub`
пользователя и технические claims времени жизни.

Telegram Mini App `initData` validation и одноразовый код через бота остаются следующими шагами.

## Последствия

- Пользовательская модель готова к будущим способам авторизации.
- Сессионные данные меньше доступны JavaScript-коду в браузере.
- Нужно аккуратно настроить cookie, CORS, CSRF-защиту и окружения dev/prod.
- Stateless session token проще внедрить на текущем этапе, но logout удаляет только cookie на клиенте.
- В будущем нужно перейти на server-side sessions через таблицу сессий или Redis и хранить в токене
  случайный `sid`, а не пользовательские идентификаторы.
