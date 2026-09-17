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

## Training Lifecycle

Сценарий `/training` проходит через bot layer как пользовательский Telegram flow,
а все данные backend получает и сохраняет через internal API.

Текущий поток:

```text
/training
  -> ensure_bot_user
  -> BotApiClient.get_training_start_context
  -> FSM draft
  -> handlers/training_units/*
  -> formatters/training.py
  -> keyboards/training_kb/*
  -> BotApiClient.save_training
  -> redirect_result.send_training_result_to_redirect_groups
  -> BotApiClient.recalculate_user_rating
```

На старте сценария бот вызывает `ensure_bot_user`, чтобы пользователь был создан
или обновлен через backend. В будущем эта точка должна стать единым guard-ом для
проверки согласия на обработку данных, блокировок и других правил доступа.

После этого бот получает стартовый контекст тренировки через
`get_training_start_context`: частые упражнения и подсказки по весу/повторениям.
Эти данные кладутся в FSM и используются только для Telegram-сценария.

Во время сценария `handlers/training_units/*` управляют переходами aiogram FSM,
а черновик тренировки изменяется через helpers из `app/bot/fsm/training`.
Текст сообщения собирается в `formatters`, кнопки собираются в `keyboards`.

При завершении сценария бот отправляет черновик в backend через `save_training`.
После успешного сохранения бот:

- обновляет сообщение в Telegram;
- отправляет результат в группы с включенным редиректом;
- запускает пересчет рейтинга через internal API.

Handlers сценария не должны:

- обращаться к БД напрямую;
- импортировать repositories;
- импортировать domain services;
- собирать SQL-запросы;
- выполнять бизнес-логику сохранения тренировки;
- создавать backend DTO напрямую внутри обработчика.

Связь между strict internal API DTO и FSM draft выполняется через adapter layer:

```text
internal API DTO -> FSM draft -> internal API DTO
```

Это позволит держать Telegram-специфичный формат состояния отдельно от контрактов
backend API.

## FSM Training Draft

Черновик тренировки в aiogram FSM хранится в одном ключе `training_draft`.
Это JSON-friendly структура, которую можно будет без изменения контрактов
перенести из `MemoryStorage` в Redis FSM storage.

Текущие верхнеуровневые FSM-ключи сценария тренировки:

```text
training_draft             основной JSON-friendly draft тренировки
changed_training_draft     JSON-friendly draft выбранной даты при смене даты
```

`training_draft` явно разделяет постоянный черновик, текущий ввод,
контекст редактирования, Telegram UI-состояние и подсказки:

```text
training:
  id: int | null
  date: YYYY-MM-DD
  comment: str | null
  exercises:
    - exercise_id: int
      exercise_name: str
      sets:
        - set_id: int | null
          set_number: int
          weight: float
          repetitions: int
          execution_time: ISO datetime | null

selection:
  mode: add_exercise | add_set | edit_set | edit_date | null
  exercise_id: int | null
  exercise_name: str | null
  weight: float | null
  repetitions: int | null
  sets_count: int | null

edit:
  exercise_id: int | null
  exercise_name: str | null
  set_id: int | null
  set_number: int | null

ui:
  message_id: int | null
  state_before_delete: str | null
  reply_markup_before_delete: JSON-compatible markup | null
  current_exercise_id: int | null
  current_exercise_name: str | null
  last_weight: float | null
  last_repetitions: int | null

suggestions:
  most_frequent_exercises: list
  weight_repetitions_modes: list
  training_dates: list[YYYY-MM-DD]
```

В целевом формате не должно быть Python-only объектов, которые нельзя напрямую
положить в Redis FSM storage или передать через JSON. Даты должны храниться строками
формата `YYYY-MM-DD`, время подходов - строками ISO datetime.

Связь FSM draft с backend должна выполняться через adapter layer:

```text
internal API DTO -> FSM training draft -> internal API DTO
```

Правила перехода:

- handlers читают и меняют draft через helpers из `app/bot/fsm/training`;
- прямой доступ к вложенным dict-ключам не допускается в handlers тренировки;
- DTO backend API не используются напрямую как FSM-хранилище;
- тесты draft helpers должны покрывать добавление упражнения, добавление подхода,
  редактирование подхода, удаление подхода и смену даты.

Internal training API больше не принимает и не возвращает старый
`training_data: dict[str, Any]`. Контракт строится вокруг строгих DTO:

```text
training:
  training_id: int | null
  training_date: YYYY-MM-DD
  comment: str | null
  exercises:
    - exercise_id: int
      exercise_name: str
      sets:
        - set_id: int | null
          set_number: int
          weight: float
          repetitions: int
          execution_time: ISO datetime | null
```

Пока domain/repository слой еще ожидает старый repository-format, преобразование
между strict DTO и repository-format допускается только внутри backend adapter
у internal training router. Bot handlers и bot API client не должны отправлять
старую FSM-структуру в API.

Старый FSM-формат `exercise_data` и переходный adapter
`legacy exercise_data <-> FSM draft` удалены из bot layer. Если после
изменения FSM-контракта в старом хранилище остались незавершенные сценарии,
их нужно сбросить и начать заново.

## Устойчивость UI Сценария Тренировки

Главное сообщение тренировки может быть удалено пользователем, а запросы к
Telegram Bot API могут завершаться ошибкой. Сценарий должен сохранять черновик
и уметь восстановить интерфейс без повторного применения пользовательского
действия.

### Источник состояния экрана

В FSM не хранятся готовые Telegram-экраны: HTML-текст, `InlineKeyboardMarkup`
и различия между версиями клавиатуры. Они являются производными данными и
каждый раз заново строятся из `TrainingDraft`.

Текущий экран определяется текущим `TrainingStates`. Для передачи шага в
renderer или временного сохранения в JSON-friendly draft используется
`TrainingFlowStep`: сериализуемый enum с теми же логическими значениями.
Например, `TrainingStates.select_weight` соответствует
`TrainingFlowStep.SELECT_WEIGHT`. Отдельное поле `current_screen` в draft не
нужно: оно дублировало бы FSM и могло бы рассинхронизироваться с ним.

`TrainingUiContext` хранит только компактный JSON-friendly контекст:

```text
ui:
  message_id: int | null
  suspended_step: TrainingFlowStep | null
  exercise_page: int
  edit_exercise_page: int
  edit_set_page: int
  calendar_year: int | null
  calendar_month: int | null
  current_exercise_id: int | null
  current_exercise_name: str | null
  last_weight: float | null
  last_repetitions: int | null
```

`suspended_step` используется временными экранами, например подтверждением
удаления и `resume_prompt`, чтобы вернуться к исходному шагу. Он заменяет
строковый `state_before_delete`. Готовая клавиатура до удаления не сохраняется:
она повторно строится renderer-ом. Данные конфликта при выборе даты также
должны быть частью типизированного `TrainingDraft`, а не отдельным ключом
`changed_training_draft` в `FSMContext`.

Параметры представления задаются явными typed-полями UI-контекста, а не общим
`screen_parameters: dict[str, Any]`. Например, для восстановления сохраняются
страница списка упражнений или открытый месяц календаря. Нельзя хранить
Telegram-объекты, текст экрана или последовательность diff-патчей. Снимок draft
мал по размеру, а повторное построение экрана не требует обращения к БД или
backend API.

### Renderer И Операции С Сообщением

Telegram UI-слой сценария тренировки разделяется на две части:

- renderer получает `TrainingDraft`, `TrainingFlowStep` и явные параметры,
  возвращает текст, клавиатуру и настройки отображения;
- message service выполняет отправку, редактирование, удаление и
  классификацию ошибок Telegram API.

Renderer не меняет FSM и draft. Все прямые вызовы `edit_text`,
`edit_message_text` и `edit_reply_markup` для главного сообщения тренировки
должны проходить через message service.

Для обратимых действий не выполняется отдельная проверка существования
сообщения редактированием тем же содержимым. Вместо этого handler строит
предполагаемые draft и целевой экран в памяти, а затем пытается сразу показать
целевой экран.

```text
Подготовить предполагаемый draft и целевой экран
  -> попытаться отредактировать главное сообщение целевым экраном
  -> успех: применить draft и FSM-переход
  -> message to edit not found: восстановить прежний экран, не применять действие
  -> другая ошибка: не применять действие и передать ошибку штатному обработчику
```

При `message is not modified` операция считается успешной. Если `message_id`
отсутствует или Telegram вернул `message to edit not found`, message service
отправляет новое сообщение с указанным экраном и сохраняет его новый id только
после успешной отправки. Ошибка `message to delete not found` считается
успешным удалением.

### Backend Действия И Актуальность Callback

Для callback-действий handler проверяет, что `callback.message.message_id`
совпадает с `draft.ui.message_id`. Это не требует нового сетевого запроса и
защищает активный сценарий от кнопок старого интерфейсного сообщения.

После успешного backend-вызова результат является источником истины. Если
показ итогового экрана не удался, сценарий сохраняет фактическое логическое
состояние и восстанавливает его при следующей `/training`; backend-вызов не
повторяется автоматически. Для успешного сохранения тренировки используется
отдельный финальный экран до очистки FSM.

Неоднозначный таймаут именно во время backend-запроса является отдельной
задачей. Для полной защиты от повторного create/update в этом случае internal
API должен будет поддержать `idempotency_key`.

### Команды Восстановления

`/training` доступна из любого состояния тренировки. Если draft отсутствует,
она запускает новый сценарий. Если draft существует, команда показывает
`resume_prompt` с вариантами продолжить или удалить черновик и не создаёт новый
draft.

`/cancel` является аварийным выходом из любого `TrainingStates`: он очищает
FSM независимо от доступности Telegram-интерфейса, после чего бот лишь
пытается удалить главное сообщение.

Во время `resume_prompt` обычный текст и неизвестные команды не должны
попадать в обработчики предыдущего шага и менять draft. Команды общего
назначения могут выполняться, не очищая черновик.

### Конкурентные Updates

На время одного перехода сценарий блокируется по паре `chat_id` и `user_id`.
В одном процессе используется локальная асинхронная блокировка. После
масштабирования bot-service на несколько экземпляров она заменяется Redis lock.

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

## FSM И Callback Values

Старые ключи FSM data для тренировки больше не используются. Telegram callback
data и aiogram state names сценария тренировки приведены к актуальному написанию.

Примеры текущих значений подтверждения:

- `accept_addition`;
- `accept_edit`;
- `delete_accepted`;
- `change_date_accept`.

Эти значения являются частью текущего протокола Telegram-сценария. При следующем
изменении callback/state values нужно обновлять handlers, keyboards и тесты
одним шагом.

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
