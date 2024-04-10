from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from typing import Dict, Union
from sqlalchemy.ext.asyncio import AsyncSession

from .training_types import TrainingStates
from utils.format_exercise_data import get_formatted_state_date
from keyboards.training_kb import ikb_finish_add_comment
from middlewares import DBSessionMiddleware
from db.database import async_session_factory
from db.queries import save_training_data



router = Router()
router.callback_query.middleware(DBSessionMiddleware(async_session_factory))



@router.callback_query(
    F.data == 'finish_training',
    TrainingStates.menu
)
async def finish_training(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Завершить тренировку"
    """
    await state.set_state(TrainingStates.add_comment)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=ikb_finish_add_comment,
    )



@router.message(TrainingStates.add_comment)
async def add_comment(message: Message, state: FSMContext):
    """
    Ввод комментария
    """
    # await state.update_data(comment=message.text)
    await message.delete()

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    user_data['exercise_data']['comment'] = message.text

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup = ikb_finish_add_comment,
    )



@router.callback_query(
    F.data == 'finish',
    TrainingStates.add_comment,
)
async def finish(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Инлайн кнопка "Завершить"
    """
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    await save_training_data(
        session=session,
        training_data=user_data.get('exercise_data')
    )

    await callback.message.edit_text(
        text=await get_formatted_state_date(state, is_result=True),
    )
    await callback.message.answer("Красава жестко!")
    await state.clear()