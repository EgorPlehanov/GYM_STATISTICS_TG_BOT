from aiogram import Router, F
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineQuery, CallbackQuery

from typing import List, Dict, Union
from datetime import datetime

from .training_states import TrainingStates
from utils.format_exercise_data import get_formatted_state_date
from utils.check_acept_addition import check_acept_addition
from keyboards import (
    get_ikb_open_inline_search,
    get_ikb_acept_addition,
)



router = Router()



@router.inline_query(TrainingStates.select_repetitions)
async def selected_additional_weight(inline_query: InlineQuery, state: FSMContext):
    """
    Инлайн выбор кол-ва повторений: возвращает список значений
    """
    def generate_numbers(substring: str) -> List[float]:
        """
        Генерирует список чисел, которые содержат substring
        """
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



@router.message(
    F.via_bot,
    TrainingStates.select_repetitions
)
async def selected_additional_weight(message: Message, state: FSMContext):
    """
    Инлайн выбор доп. веса: обработка выбранного значения
    """
    await state.set_state(TrainingStates.acept_addition)

    repetitions = int(message.text)
    await state.update_data(repetitions=repetitions)
    await message.delete()

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_acept_addition(user_data.get('mode'))
    )



@router.callback_query(F.data == "to_repetitions", TrainingStates.select_weight)
@router.callback_query(F.data == "to_repetitions", TrainingStates.acept_addition)
async def to_repetitions(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Вперед Повторения" переход к повторениям
    """
    await state.set_state(TrainingStates.select_repetitions)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "повторения",
            back_button_text="Вес",
            back_button_callback_data="to_weight",
            has_acept_addition_button = await check_acept_addition(state)
        ),
    )