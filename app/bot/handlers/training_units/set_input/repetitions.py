from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    TrainingMode,
    TrainingStates,
    accept_button_by_mode,
    check_accept_addition,
    get_training_draft,
    get_weight_repetitions_modes_values_from_draft,
    set_training_draft,
)
from app.bot.keyboards.training_kb import (
    get_ikb_accept_addition,
    get_ikb_open_inline_search,
)

router = Router()



r_int = r"\d+"
r_repetitions = rf"^\s*{r_int}\s*$"



@router.inline_query(TrainingStates.select_repetitions)
async def inline_repetitions(inline_query: InlineQuery, state: FSMContext):
    """Возвращает inline-подсказки для выбора количества повторений."""
    def generate_numbers(substring: str) -> list[int]:
        """Генерирует значения повторений, которые содержат введенную подстроку."""
        numbers = []
        for number in range(0, 1001):
            if str(number).find(substring) != -1:
                numbers.append(number)
        return numbers
    
    offset = int(inline_query.offset) if inline_query.offset else 0
    
    results = []
    for number in generate_numbers(inline_query.query):
        results.append(
            InlineQueryResultArticle(
                id=str(number),
                title=f"{number} повторений",
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
            is_personal=True
        )



@router.message(F.via_bot, TrainingStates.select_repetitions)
@router.message(F.text.regexp(r_repetitions), TrainingStates.select_repetitions)
async def selected_repetitions(message: Message, state: FSMContext):
    """Сохраняет выбранное количество повторений."""
    await state.set_state(TrainingStates.accept_addition)

    repetitions = int(message.text)
    draft = await get_training_draft(state)
    draft.selection.repetitions = repetitions
    await set_training_draft(state, draft)
    await message.delete()

    mode = TrainingMode(draft.selection.mode)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=draft.ui.message_id,
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_accept_addition(mode)
    )



@router.callback_query(F.data == "to_repetitions", TrainingStates.select_weight)
@router.callback_query(F.data == "to_repetitions", TrainingStates.select_sets_count)
@router.callback_query(F.data == "to_repetitions", TrainingStates.accept_addition)
async def to_repetitions(callback: CallbackQuery, state: FSMContext):
    """Переводит сценарий к выбору количества повторений."""
    await state.set_state(TrainingStates.select_repetitions)

    draft = await get_training_draft(state)
    mode = TrainingMode(draft.selection.mode)
    accept_button = accept_button_by_mode.get(mode)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "повторения",
            back_button_text = "Вес",
            back_button_callback_data = "to_weight",
            has_next_button = (
                draft.selection.repetitions is not None
                and mode != TrainingMode.EDIT_SET
            ),
            next_button_text = "Кол-во подходов",
            next_button_callback_data = "to_sets_count",
            has_accept_button = await check_accept_addition(state),
            accept_button_text = accept_button.text,
            accept_button_callback_data = accept_button.callback_data,
            has_delete_set_button = mode == TrainingMode.EDIT_SET,
            switch_inline_query = get_weight_repetitions_modes_values_from_draft(
                draft,
                is_repetitions=True,
            )
        ),
    )

