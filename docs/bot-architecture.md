# Архитектура Telegram-бота

## Назначение

Telegram-бот является отдельным UI-сервисом проекта.

Он отвечает за Telegram-специфичную часть приложения:

- прием Telegram updates;
- маршрутизацию команд, сообщений, callback query и inline query;
- управление aiogram FSM;
- построение Telegram-клавиатур;
- форматирование сообщений;
- вызовы backend через internal API;
- обработку Telegram-специфичных ошибок.

Бот не должен выполнять SQL-запросы, обращаться к repositories или вызывать domain services напрямую.

Целевой поток:

```text
Telegram Update
  -> bot handler
  -> FSM draft / formatter / keyboard
  -> BotApiClient
  -> FastAPI internal API
  -> domain service
  -> repository
  -> database
```

Такой подход делает Telegram Bot и будущий web frontend равноправными клиентами backend API.

## Границы ответственности

### Handlers

Handlers являются входными точками Telegram-событий.

Они должны:

- принимать событие от aiogram;
- извлекать минимально нужный контекст;
- вызывать `BotApiClient`, FSM helpers, formatters и keyboards;
- отправлять или редактировать Telegram-сообщения.

Handlers не должны содержать SQL-запросы, сложные бизнес-правила и большие преобразования данных.

### API client

`app/bot/api_client` является единственной границей между ботом и backend.

Он должен:

- вызывать `/internal/*` endpoints;
- передавать service-to-service token;
- преобразовывать JSON-ответы internal API в bot DTO;
- скрывать детали HTTP от handlers.

API client не должен форматировать Telegram-сообщения и управлять FSM-сценариями.

### FSM

FSM-слой хранит Telegram-состояния и черновики пользовательских сценариев.

Для сценария тренировки целевая структура должна описывать JSON-friendly draft:

- дата тренировки;
- упражнения;
- подходы;
- текущий выбранный режим;
- временные значения текущего ввода.

FSM draft должен быть пригоден для хранения в Redis и передачи через JSON без ручной сериализации в handlers.

### Keyboards

Keyboards отвечают только за сборку Telegram-клавиатур.

Они должны получать готовые данные для отображения и возвращать `InlineKeyboardMarkup` или другие Telegram markup-объекты.

Keyboards не должны обращаться к API, БД, domain services или самостоятельно менять FSM.

### Formatters

Formatters отвечают за текстовое представление данных в Telegram.

Они должны:

- формировать текст тренировки;
- формировать текст статистики;
- формировать admin/error-сообщения;
- учитывать ограничения Telegram по длине сообщений.

Formatters не должны изменять данные сценария.

### Filters

Filters отвечают за условия маршрутизации aiogram.

Примеры:

- проверка роли администратора;
- проверка типа чата;
- проверка наличия значения в FSM.

Если проверка требует данных backend, filter должен обращаться через internal API, а не напрямую к БД.

### Middlewares

Middlewares отвечают за поперечную Telegram-логику.

Допустимые примеры:

- отправка chat action;
- добавление контекста логирования;
- единая обработка технического контекста запроса.

DB middleware в bot layer не используется, потому что бот не должен открывать DB session.

### Utils

`utils` должен оставаться местом только для маленьких независимых функций, которые не знают про конкретный сценарий.

Если функция знает про тренировку, FSM, export, redirect или admin-сценарий, она должна лежать в соответствующем feature-пакете, а не в общем `utils`.

## Целевая структура

```text
app/bot/
  main.py
  client.py

  api_client/
    base.py
    users.py
    trainings.py
    exercises.py
    statistics.py
    export.py
    groups.py
    admin.py
    schemas/

  handlers/
    common/
    training/
    statistics/
    export/
    redirect/
    groups/
    admin/

  keyboards/
    common/
    training/
    redirect/
    admin/

  fsm/
    training/
      states.py
      draft.py
      adapters.py

  formatters/
    training.py
    statistics.py
    errors.py
    export.py

  filters/
    main_admin.py
    state_attribute.py

  middlewares/
    chat_action.py
    error_context.py

  utils/
    split_message.py
    number_to_emojis.py
```

## Сценарий тренировки

Сценарий тренировки является самым сложным сценарием бота, поэтому его нужно развивать как feature-модуль.

Целевое разделение:

- `handlers/training` - Telegram-обработчики сценария;
- `fsm/training` - состояния, draft и адаптеры сериализации;
- `keyboards/training` - клавиатуры сценария;
- `formatters/training.py` - текстовое представление тренировки;
- `api_client/trainings.py` - вызовы internal training API.

Handlers сценария должны работать с draft через helper-функции, а не напрямую менять вложенные словари через строковые ключи.

## Inline payload

Inline payload не должен зависеть от runtime-only ключа, созданного при старте процесса.

Недопустимый долгосрочный вариант:

```text
Fernet.generate_key() при старте bot process
```

Такой ключ теряется при рестарте контейнера и не подходит для масштабирования.

Целевые варианты:

- signed payload с постоянным секретом из env;
- короткий payload id с хранением данных в Redis TTL.

Окончательный выбор нужно сделать вместе с внедрением Redis и переводом FSM storage.

## Правила импортов

`app/bot` может импортировать:

- `app.bot.*`;
- `app.core.config`;
- DTO и helpers, предназначенные для bot layer.

`app/bot` не должен импортировать:

- `app.db.*`;
- `app.domain.*`;
- SQLAlchemy session;
- repositories.

Исключения возможны только для временных переходных задач и должны быть зафиксированы в backlog.

## Связь с web frontend

Telegram Bot, Web SPA и Telegram Mini App должны использовать одну бизнес-реализацию через backend API.

Различаться могут:

- способ авторизации;
- DTO внешнего интерфейса;
- форма пользовательского сценария;
- ограничения UI.

Не должна различаться доменная логика создания, редактирования, удаления тренировок и получения статистики.
