from aiogram import Router, F
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineQuery, CallbackQuery

from typing import List, Dict, Union

from .training_states import TrainingStates
from utils.check_acept_addition import check_acept_addition
from utils.format_exercise_data import get_formatted_state_date
from keyboards import (
    get_ikb_open_inline_search,
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


    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    if user_data.get('mode') != 'add_exercise':
        await state.update_data(mode='add_set')

    await state.update_data(cur_exercise_id=user_data.get('exercise_id'))
    await state.update_data(cur_exercise_name=user_data.get('exercise_name'))

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            has_next_button = user_data.get("weight") is not None,
            next_button_text = "Повторения",
            next_button_callback_data = "to_repetitions",
        ),
    )



@router.inline_query(TrainingStates.select_weight)
async def selected_additional_weight(inline_query: InlineQuery, state: FSMContext):
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



@router.message(
    F.via_bot,
    TrainingStates.select_weight
)
async def selected_additional_weight(message: Message, state: FSMContext):
    """
    Инлайн выбор доп. веса: обработка выбранного значения
    """
    await state.set_state(TrainingStates.select_repetitions)

    await state.update_data(weight=float(message.text))
    await message.delete()

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_open_inline_search(
            entity_name = "повторения",
            back_button_text="Вес",
            back_button_callback_data="to_weight",
            has_acept_addition_button = await check_acept_addition(state)
        ),
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

    back_button_text = {
        "add_exercise": "Упражнение",
        "add_set": "Меню",
    }
    back_button_callback_data = {
        "add_exercise": "to_exercise",
        "add_set": "to_menu",
    }
    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            back_button_text=back_button_text.get(user_data.get('mode')),
            back_button_callback_data=back_button_callback_data.get(user_data.get('mode')),
            has_next_button=user_data.get("weight") is not None,
            next_button_text="Повторения",
            next_button_callback_data="to_repetitions",
            has_acept_addition_button = await check_acept_addition(state)
        ),
    )