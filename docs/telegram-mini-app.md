# Telegram Mini App

Telegram Mini App - это web frontend, который открывается внутри Telegram WebView и получает данные запуска от Telegram.

## Режимы работы web frontend

Web должен поддерживать два режима:

- обычный браузер;
- Telegram Mini App.

## Авторизация в Mini App

Frontend получает `window.Telegram.WebApp.initData` и отправляет его на backend:

```text
React/Vite -> POST /api/auth/telegram-mini-app -> FastAPI
```

Тело запроса:

```json
{
  "init_data": "query_id=...&user=...&auth_date=...&hash=..."
}
```

Backend проверяет подпись `initData` через `TG_BOT_TOKEN`. Только после серверной проверки пользователь считается авторизованным.

`initDataUnsafe` можно использовать только для UI-подсказок на клиенте. Его нельзя считать доверенным источником.

## UI-особенности

Frontend должен учитывать:

- mobile-first layout;
- Telegram light/dark theme params;
- Telegram BackButton;
- Telegram MainButton;
- safe area;
- viewport height внутри WebView;
- ограничения мобильного WebView.

## Настройка

Инструкция настройки Mini App через BotFather будет добавлена после появления frontend-сборки и публичного URL.
