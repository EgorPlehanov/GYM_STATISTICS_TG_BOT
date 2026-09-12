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
- собирать простые файлы пользовательского представления, если они нужны только Telegram-сценарию;
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

### Keyboard Naming

В текущей версии проекта inline-клавиатуры Telegram-бота именуются с префиксом `ikb_`.

Правило применяется к файлам и публичным функциям фабрик:

- файл: `ikb_select_exercise.py`;
- функция: `get_ikb_select_exercise_fab`;
- объект готовой клавиатуры: `ikb_edit_accept_delete`.

Это локальная конвенция проекта, а не обязательный стандарт aiogram. Она сохраняется,
потому что уже используется в кодовой базе и помогает быстро отличать inline-клавиатуры
от других Telegram UI-сущностей.

Если в будущем появятся reply-клавиатуры или потребуется более явное именование,
можно отдельно рассмотреть переход на `inline_keyboard`/`reply_keyboard` в именах
пакетов или функций. Такой переход должен выполняться отдельным рефакторингом.

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
      date.py
      exercise.py
      set_input/
      edit/
      finish.py
    statistics/
    export/
    redirect/
    groups/
    admin/

  keyboards/
    common/
    training/
      ikb_training_menu.py
      date/
      exercise/
      set_input/
      edit/
      ikb_finish_add_comment.py
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
    messages.py
    errors.py
    export.py

  filters/
    main_admin.py
    state_attribute.py

  middlewares/
    chat_action.py
    error_context.py

  utils/
    user_access.py
    migration_cache.py
```

## Сценарий тренировки

Сценарий тренировки является самым сложным сценарием бота, поэтому его нужно развивать как feature-модуль.

Целевое разделение:

- `handlers/training` - входная команда `/training` и общая сборка router-ов;
- `handlers/training_units/date.py` - выбор и смена даты тренировки;
- `handlers/training_units/exercise.py` - выбор упражнения;
- `handlers/training_units/set_input/` - ввод веса, повторений, количества подходов и подтверждение добавления;
- `handlers/training_units/edit/` - меню редактирования, выбор упражнения и подхода;
- `handlers/training_units/finish.py` - комментарий, сохранение и завершение тренировки;
- `fsm/training` - состояния, draft и адаптеры сериализации;
- `keyboards/training_kb/ikb_training_menu.py` - главное меню тренировки;
- `keyboards/training_kb/date/` - выбор даты и календарь;
- `keyboards/training_kb/exercise/` - выбор упражнения;
- `keyboards/training_kb/set_input/` - ввод веса, повторений, количества подходов и подтверждение добавления;
- `keyboards/training_kb/edit/` - клавиатуры редактирования и подтверждения удаления;
- `keyboards/training_kb/ikb_finish_add_comment.py` - клавиатура комментария и завершения;
- `formatters/training.py` - текстовое представление тренировки;
- `api_client/trainings.py` - вызовы internal training API.

Handlers сценария должны работать с draft через helper-функции, а не напрямую менять вложенные словари через строковые ключи.

Текущие состояния и режимы сценария хранятся в `app/bot/fsm/training/states.py`.
Legacy state names внутри `TrainingStates` сохраняются до отдельного шага перевода на
строгий FSM draft.

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

## Legacy FSM и callback values

До полного рефакторинга FSM допускается сохранять старые значения Telegram callback data,
aiogram state names и ключи FSM data.

Примеры старых значений:

- `acept_addition`;
- `acept_edit`;
- `delete_acepted`;
- `delete_acept_flag`;
- `change_date_acept`.

Эти значения являются частью текущего протокола Telegram-сценария. Их нужно менять
отдельным шагом вместе с переводом сценария тренировки на строгий FSM draft, чтобы не
сломать текущие callback handlers и восстановление состояния.

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

## Export-файлы

Текущая простая XLSX-выгрузка для команды Telegram-бота является presentation helper
и может жить в `app/bot/formatters/export.py`.

Если Excel-экспорт станет сложным продуктовым артефактом или понадобится не только
боту, генератор нужно вынести из bot layer в общий backend-модуль:

```text
app/export/excel/
  builder.py
  sheets.py
  styles.py
  charts.py
  templates/
```

`domain/export` отвечает за состав данных, права и фильтры экспорта. Общий
`app/export/excel` отвечает за представление файла: листы, стили, формулы, графики
и шаблоны.

Если генерация станет долгой, API должен ставить задачу, а файл должен собирать
worker. Telegram-бот и web frontend в таком сценарии только запрашивают экспорт и
получают готовый файл через backend API.
