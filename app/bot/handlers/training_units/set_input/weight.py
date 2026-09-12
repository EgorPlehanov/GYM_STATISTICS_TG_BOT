import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from app.bot.filters import StateAttributeNotNoneFilter
from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    Button,
    TrainingMode,
    TrainingStates,
    accept_button_by_mode,
    check_accept_addition,
    get_training_draft,
    get_weight_repetitions_modes_values,
    set_training_draft,
    weight_back_button_by_mode,
)
from app.bot.keyboards.training_kb import (
    get_ikb_accept_addition,
    get_ikb_open_inline_search,
)

router = Router()



r_float = r"\d+([.,]?\d+)?"
r_int = r"\d+"
r_separator = r"\s*[*×xх]\s*"
r_weight = rf"^\s*{r_float}\s*$"
r_weight_repetitions_sets = rf"^\s*{r_float}{r_separator}{r_int}({r_separator}{r_int})?\s*$"



@router.callback_query(
    F.data == 'add_set',
    TrainingStates.menu
)
async def add_set_handler(callback: CallbackQuery, state: FSMContext):
    """Открывает ввод нового подхода для текущего упражнения."""
    await state.set_state(TrainingStates.select_weight)

    user_data: dict[str, int | dict] = await state.get_data()
    draft = await get_training_draft(state)
    draft.selection.mode = TrainingMode.ADD_SET.value
    draft.selection.exercise_id = user_data.get("exercise_id")
    draft.selection.exercise_name = user_data.get("exercise_name")
    draft.selection.sets_count = 1
    await set_training_draft(state, draft)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            has_next_button = user_data.get("weight") is not None,
            next_button_text = "Повторения",
            next_button_callback_data = "to_repetitions",
            has_delete_set_button = False,
            switch_inline_query = get_weight_repetitions_modes_values(
                user_data = await state.get_data(),
                is_weight = True
            )
        ),
    )



@router.inline_query(TrainingStates.select_weight)
async def inline_weight(inline_query: InlineQuery, state: FSMContext):
    """Возвращает inline-подсказки для выбора веса."""
    def generate_numbers(substring: str) -> list[float]:
        """Генерирует значения веса, которые содержат введенную подстроку."""
        numbers = []
        for i in range(0, 50100, 25):
            number = i / 100
            if str(number).find(substring) != -1:
                numbers.append(number)
        return numbers
    
    offset = int(inline_query.offset) if inline_query.offset else 0
    
    results = []
    for number in generate_numbers(inline_query.query):
        results.append(
            InlineQueryResultArticle(
                id=str(number),
                title=f"{number:.2f} кг",
                input_message_content=InputTextMessageContent(
                    message_text = str(number)
                ),
            )
        )

    if len(results) < 50:
        await inline_query.answer(
            results,
            cache_time = 0,
            is_personal=True
        )
    else:
        await inline_query.answer(
            results[offset:offset+50],
            next_offset=str(offset+50),
            cache_time = 0,
            is_personal=True,
        )



@router.message(F.via_bot, TrainingStates.select_weight)
@router.message(F.text.regexp(r_weight), TrainingStates.select_weight)
async def selected_weight(message: Message, state: FSMContext):
    """Сохраняет выбранный вес и переводит сценарий к вводу повторений."""
    weight = float(message.text.replace(',', '.'))

    await state.set_state(TrainingStates.select_repetitions)

    draft = await get_training_draft(state)
    draft.selection.weight = weight
    await set_training_draft(state, draft)
    await message.delete()

    user_data: dict[str, int | dict] = await state.get_data()

    accept_button = accept_button_by_mode.get(user_data.get('mode'))

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_open_inline_search(
            entity_name = "повторения",
            back_button_text = "Вес",
            back_button_callback_data = "to_weight",
            has_next_button = (
                user_data.get("repetitions") is not None
                and user_data.get("mode") != TrainingMode.EDIT_SET
            ),
            next_button_text = "Кол-во подходов",
            next_button_callback_data = "to_sets_count",
            has_accept_button = await check_accept_addition(state),
            accept_button_text = accept_button.text,
            accept_button_callback_data = accept_button.callback_data,
            has_delete_set_button = user_data.get("mode") == TrainingMode.EDIT_SET,
            switch_inline_query = get_weight_repetitions_modes_values(
                user_data, is_repetitions=True
            )
        ),
    )



@router.message(
    StateAttributeNotNoneFilter("exercise_id"),
    F.text.regexp(r_weight_repetitions_sets, flags=re.IGNORECASE),
    TrainingStates.menu
)
@router.message(
    F.text.regexp(r_weight_repetitions_sets, flags=re.IGNORECASE),
    TrainingStates.select_weight
)
@router.message(
    F.text.regexp(r_weight_repetitions_sets, flags=re.IGNORECASE),
    TrainingStates.select_repetitions
)
@router.message(
    F.text.regexp(r_weight_repetitions_sets, flags=re.IGNORECASE),
    TrainingStates.select_sets_count
)
@router.message(
    F.text.regexp(r_weight_repetitions_sets, flags=re.IGNORECASE),
    TrainingStates.acept_addition
)
async def read_weight_and_repetitions(message: Message, state: FSMContext):
    """Обрабатывает ручной ввод веса, повторений и опционально количества подходов."""
    await message.delete()

    values = re.split(r_separator, message.text, flags=re.IGNORECASE)

    if len(values) == 3:
        weight, repetitions, sets_count = values
    else:
        weight, repetitions = values
        sets_count = None
    
    weight = float(weight.replace(',', '.'))
    repetitions = int(repetitions)
    sets_count = int(sets_count) if sets_count is not None and int(sets_count) > 0 else None

    user_data: dict[str, int | dict] = await state.get_data()
    draft = await get_training_draft(state)
    mode = TrainingMode(draft.selection.mode) if draft.selection.mode else None

    # Если значение введено в меню тренировки
    if mode is None:
        mode = TrainingMode.ADD_SET
        draft.selection.mode = TrainingMode.ADD_SET.value
        draft.selection.exercise_id = user_data.get("exercise_id")
        draft.selection.exercise_name = user_data.get("exercise_name")
        draft.selection.sets_count = 1

    if (
        weight == draft.selection.weight
        and repetitions == draft.selection.repetitions
        and (
            sets_count is not None and sets_count == draft.selection.sets_count
            or sets_count is None
        )
        and await state.get_state() == TrainingStates.acept_addition
    ):
        return
    
    await state.set_state(TrainingStates.acept_addition)

    draft.selection.weight = weight
    draft.selection.repetitions = repetitions
    if sets_count is not None:
        draft.selection.sets_count = sets_count
    await set_training_draft(state, draft)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_accept_addition(mode)
    )
        


@router.callback_query(F.data == "to_weight", TrainingStates.select_exercise)
@router.callback_query(F.data == "to_weight", TrainingStates.select_repetitions)
@router.callback_query(F.data == "to_weight", TrainingStates.acept_addition)
async def to_weight(callback: CallbackQuery, state: FSMContext):
    """Переводит сценарий к выбору веса."""
    await state.set_state(TrainingStates.select_weight)

    draft = await get_training_draft(state)
    mode = TrainingMode(draft.selection.mode)
    user_data: dict[str, int | dict] = await state.get_data()

    back_button: Button = weight_back_button_by_mode.get(mode)
    accept_button = accept_button_by_mode.get(mode)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            back_button_text = back_button.text,
            back_button_callback_data = back_button.callback_data,
            has_next_button = user_data.get("weight") is not None,
            next_button_text = "Повторения",
            next_button_callback_data = "to_repetitions",
            has_accept_button = await check_accept_addition(state),
            accept_button_text = accept_button.text,
            accept_button_callback_data = accept_button.callback_data,
            has_delete_set_button = mode == TrainingMode.EDIT_SET,
            switch_inline_query = get_weight_repetitions_modes_values(
                user_data, is_weight=True
            )
        ),
    )



@router.callback_query(F.data == "repeat_set", TrainingStates.menu)
async def repeat_set(callback: CallbackQuery, state: FSMContext):
    """Предлагает повторить последний сохраненный подход текущего упражнения."""
    await state.set_state(TrainingStates.acept_addition)

    user_data: dict[str, int | dict] = await state.get_data()
    draft = await get_training_draft(state)
    draft.selection.mode = TrainingMode.ADD_SET.value
    draft.selection.exercise_id = user_data.get("exercise_id")
    draft.selection.exercise_name = user_data.get("exercise_name")
    draft.selection.sets_count = 1
    draft.selection.weight = user_data.get("last_weight")
    draft.selection.repetitions = user_data.get("last_repetitions")
    await set_training_draft(state, draft)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_accept_addition(TrainingMode.ADD_SET)
    )

