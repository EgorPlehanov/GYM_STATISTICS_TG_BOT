from aiogram import Router, F
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineQuery, CallbackQuery

from typing import List, Dict, Union
import re

from .training_types import (
    TrainingStates,
    TrainingMode,
    Button,
    weight_back_button_by_mode,
    acept_button_by_mode
)
from utils.check_acept_addition import check_acept_addition
from utils.format_exercise_data import get_formatted_state_date
from keyboards import (
    get_ikb_open_inline_search,
    get_ikb_acept_addition,
)



router = Router()



@router.callback_query(
    F.data == 'add_set',
    TrainingStates.menu
)
async def add_set_handler(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Добавить повторение"
    """
    await state.set_state(TrainingStates.select_weight)

    await state.update_data(mode=TrainingMode.ADD_SET)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    await state.update_data(cur_exercise_id=user_data.get('exercise_id'))
    await state.update_data(cur_exercise_name=user_data.get('exercise_name'))

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            has_next_button = user_data.get("weight") is not None,
            next_button_text = "Повторения",
            next_button_callback_data = "to_repetitions",
            has_delete_set_button = False
        ),
    )



@router.inline_query(TrainingStates.select_weight)
async def inline_additional_weight(inline_query: InlineQuery, state: FSMContext):
    """
    Инлайн выбор доп. веса: возвращает список значений
    """
    def generate_numbers(substring: str) -> List[float]:
        """
        Генерирует список чисел, которые содержат substring
        """
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
@router.message(F.text.regexp(r'^\d+([.,]?\d+)?$'), TrainingStates.select_weight)
async def selected_additional_weight(message: Message, state: FSMContext):
    """
    Инлайн выбор доп. веса: обработка выбранного значения
    """
    weight = float(message.text.replace(',', '.'))

    await state.set_state(TrainingStates.select_repetitions)
    
    await state.update_data(weight=weight)
    await message.delete()

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    acept_button = acept_button_by_mode.get(user_data.get('mode'))

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_open_inline_search(
            entity_name = "повторения",
            back_button_text="Вес",
            back_button_callback_data="to_weight",
            has_acept_button = await check_acept_addition(state),
            acept_button_text = acept_button.text,
            acept_button_callback_data = acept_button.callback_data,
            has_delete_set_button = user_data.get("mode") == TrainingMode.EDIT_SET
        ),
    )



@router.message(F.text.regexp(r'^\d+([.,]?\d+)?\s*[*×xXхХ]\s*\d+$'), TrainingStates.select_weight)
@router.message(F.text.regexp(r'^\d+([.,]?\d+)?\s*[*×xXхХ]\s*\d+$'), TrainingStates.select_repetitions)
@router.message(F.text.regexp(r'^\d+([.,]?\d+)?\s*[*×xXхХ]\s*\d+$'), TrainingStates.acept_addition)
async def read_weight_and_repetitions(message: Message, state: FSMContext):
    """
    Обработка ввода веса и повторений
    """
    await message.delete()

    weight, repetitions = re.split(r'\s*[*×xXхХ]\s*', message.text)
    weight = float(weight.replace(',', '.'))
    repetitions = int(repetitions)

    await state.set_state(TrainingStates.acept_addition)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    if (
        weight == user_data.get('weight')
        and repetitions == user_data.get('repetitions')
        and await state.get_state == "TrainingStates.acept_addition"
    ):
        return

    await state.update_data(weight=weight, repetitions=repetitions)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_acept_addition(user_data.get('mode'))
    )



@router.callback_query(F.data == "to_weight", TrainingStates.select_exercise)
@router.callback_query(F.data == "to_weight", TrainingStates.select_repetitions)
@router.callback_query(F.data == "to_weight", TrainingStates.acept_addition)
async def to_weight(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Вперед Вес" переход к весу
    """
    await state.set_state(TrainingStates.select_weight)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    back_button: Button = weight_back_button_by_mode.get(user_data.get('mode'))
    acept_button = acept_button_by_mode.get(user_data.get('mode'))

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            back_button_text=back_button.text,
            back_button_callback_data=back_button.callback_data,
            has_next_button=user_data.get("weight") is not None,
            next_button_text="Повторения",
            next_button_callback_data="to_repetitions",
            has_acept_button = await check_acept_addition(state),
            acept_button_text = acept_button.text,
            acept_button_callback_data = acept_button.callback_data,
            has_delete_set_button = user_data.get("mode") == TrainingMode.EDIT_SET
        ),
    )