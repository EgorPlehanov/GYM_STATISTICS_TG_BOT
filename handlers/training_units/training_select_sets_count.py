from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineQuery,
    InlineQueryResultArticle, InputTextMessageContent, 
)
from aiogram.fsm.context import FSMContext

from typing import List, Dict, Union

from .training_types import TrainingStates, TrainingMode, acept_button_by_mode
from utils.format_exercise_data import get_formatted_state_date
from utils.check_acept_addition import check_acept_addition
from keyboards.training_kb import (
    get_ikb_open_inline_search,
    get_ikb_acept_addition,
)



router = Router()



@router.inline_query(TrainingStates.select_sets_count)
async def inline_sets_count(inline_query: InlineQuery, state: FSMContext):
    """
    Инлайн выбор кол-ва подходов
    """
    def generate_numbers(substring: str) -> List[float]:
        """
        Генерирует список чисел, которые содержат substring
        """
        numbers = []
        for number in range(1, 101):
            if str(number).find(substring) != -1:
                numbers.append(number)
        return numbers
    
    offset = int(inline_query.offset) if inline_query.offset else 0
    
    results = []
    for number in generate_numbers(inline_query.query):
        results.append(
            InlineQueryResultArticle(
                id=str(number),
                title=f"{number} подходов",
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



@router.message(F.via_bot, TrainingStates.select_sets_count)
@router.message(F.text.regexp(r'^\d+$'), TrainingStates.select_sets_count)
async def selected_sets_count(message: Message, state: FSMContext):
    """
    Инлайн выбор доп. веса: обработка выбранного значения
    """
    await state.set_state(TrainingStates.acept_addition)

    sets_count = int(message.text)
    await state.update_data(sets_count=sets_count)
    await message.delete()

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_acept_addition(user_data.get('mode'))
    )



@router.callback_query(F.data == "to_sets_count", TrainingStates.select_repetitions)
@router.callback_query(F.data == "to_sets_count", TrainingStates.acept_addition)
async def to_repetitions(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Переход к Повторениям" переход к повторениям
    """
    await state.set_state(TrainingStates.select_sets_count)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    acept_button = acept_button_by_mode.get(user_data.get('mode'))

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "кол-во подходов",
            back_button_text="Повторения",
            back_button_callback_data="to_repetitions",
            has_acept_button = await check_acept_addition(state),
            acept_button_text = acept_button.text,
            acept_button_callback_data = acept_button.callback_data,
            has_delete_set_button = user_data.get("mode") == TrainingMode.EDIT_SET
        ),
    )