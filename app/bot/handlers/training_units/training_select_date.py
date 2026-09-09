from datetime import datetime

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.client import BotApiClient
from app.bot.keyboards.training_kb import (
    DialogCalendar,
    DialogCalendarCallback,
    get_ikb_changed_date,
    get_ikb_select_date,
    get_ikb_training_menu,
)
from app.bot.utils.format_training_data import get_formatted_state_date

from .training_types import TrainingMode, TrainingStates

router = Router()



async def init_training_by_date(
    date: datetime,
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Инициализирует тренировку по дате
    """
    async with BotApiClient() as api_client:
        result = await api_client.get_training_by_date(
            telegram_id=callback.from_user.id,
            training_date=date,
        )
    changed_exercise_data = result.training_data
    is_exists = result.exists

    user_data: dict[str, int | dict] = await state.get_data()
    cur_exercise_data = user_data.get('exercise_data')
    if cur_exercise_data is None:
        await state.update_data(exercise_data=changed_exercise_data)
    else:
        if cur_exercise_data.get('date').date() == date.date():
            return
        if is_exists:
            await state.set_state(TrainingStates.change_date_acept)
            await state.update_data(changed_exercise_data=changed_exercise_data)
            await callback.message.edit_text(
                text=await get_formatted_state_date(state),
                reply_markup = get_ikb_changed_date(
                    other_date=date
                )
            )
            return False
        else:
            cur_exercise_data['date'] = date



@router.callback_query(
    F.data == 'today',
    TrainingStates.select_date
)
async def selected_date_today(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Инлайн кнопка "Сегодня"
    """
    await state.set_state(TrainingStates.menu)
    await state.update_data(mode=None)

    date = datetime.now()

    if (await init_training_by_date(date, callback, state)) is False:
        return

    user_data: dict[str, int | dict] = await state.get_data()
    exercises = user_data.get('exercise_data')['exercises']

    last_weight = str(user_data.get('last_weight', '')).rstrip('0').rstrip(".")
    last_repetitions = user_data.get('last_repetitions', '')

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_training_menu(
            is_add_edit_button = len(exercises) != 0,
            is_add_add_set_button = user_data.get("exercise_id") is not None,
            repeat_set_button_text = f"{last_weight}×{last_repetitions}"
        ),
    )



@router.callback_query(
    F.data == 'other_date',
    TrainingStates.select_date
)
async def selected_date_other(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Инлайн кнопка "Другая дата"
    """
    user_data = await state.get_data()
    if user_data.get('training_date') is None:
        async with BotApiClient() as api_client:
            training_date = await api_client.get_training_dates(callback.from_user.id)
        await state.update_data(training_date=training_date)
    else:
        training_date = user_data.get('training_date')

    await callback.message.edit_reply_markup(
        reply_markup=await DialogCalendar(training_date=training_date).start_calendar()
    )



@router.callback_query(
    DialogCalendarCallback.filter()
)
async def process_dialog_calendar(
    callback: CallbackQuery,
    callback_data: CallbackData,
    state: FSMContext,
) -> None:
    """
    Обработка выбора даты в инлайн календаре
    """
    user_data = await state.get_data()

    selected, date = await DialogCalendar(
        training_date=user_data.get('training_date')
    ).process_selection(callback, callback_data)

    if selected:
        await state.set_state(TrainingStates.menu)
        await state.update_data(mode=None)

        if (await init_training_by_date(date, callback, state)) is False:
            return

        user_data: dict[str, int | dict] = await state.get_data()
        exercises = user_data.get('exercise_data')['exercises']

        last_weight = str(user_data.get('last_weight', '')).rstrip('0').rstrip(".")
        last_repetitions = user_data.get('last_repetitions', '')

        await callback.message.edit_text(
            text=await get_formatted_state_date(state),
            reply_markup = get_ikb_training_menu(
                is_add_edit_button = len(exercises) != 0,
                is_add_add_set_button = user_data.get("exercise_id") is not None,
                repeat_set_button_text = f"{last_weight}×{last_repetitions}"
            ),
        )



@router.callback_query(F.data == 'to_date_menu', TrainingStates.select_date)
@router.callback_query(F.data == 'to_date_menu', TrainingStates.change_date_acept)
async def back_to_date_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Инлайн кнопка "Меню даты" возврат в меню
    """
    await state.set_state(TrainingStates.select_date)

    user_data: dict[str, int | dict] = await state.get_data()
    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(
            is_back_to_menu=user_data.get('exercise_data') is not None,
        ),
    )
    


@router.callback_query(
    F.data == 'edit_date',
    TrainingStates.edit_menu
)
async def open_edit_date(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Редактировать дату"
    """
    await state.set_state(TrainingStates.select_date)

    await state.update_data(mode=TrainingMode.EDIT_DATE)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(is_back_to_menu=True),
    )



@router.callback_query(
    F.data == 'save_and_go',
    TrainingStates.change_date_acept
)
async def save_and_go(callback: CallbackQuery, state: FSMContext):
    """
    Сохраняет текущую тренировку и переходит к выбранной
    """
    user_data: dict[str, int | dict] = await state.get_data()
    exercise_data = user_data.get('exercise_data')
    async with BotApiClient() as api_client:
        await api_client.save_training(exercise_data)

    changed_exercise_data = user_data.get('changed_exercise_data')
    await state.update_data(exercise_data=changed_exercise_data)
    await state.update_data(changed_exercise_data=None)
    await state.update_data(exercise_id=None)
    await state.update_data(exercise_name=None)

    await state.set_state(TrainingStates.menu)
    exercises = changed_exercise_data.get('exercises', {})

    last_weight = str(user_data.get('last_weight', '')).rstrip('0').rstrip(".")
    last_repetitions = user_data.get('last_repetitions', '')

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_training_menu(
            is_add_edit_button = len(exercises) != 0,
            is_add_add_set_button = False,
            repeat_set_button_text = f"{last_weight}×{last_repetitions}"
        ),
    )




@router.callback_query(
    F.data == 'changed_to_current_date',
    TrainingStates.change_date_acept
)
async def changed_to_current_date(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка заменить тренировку на текущую
    """
    await state.set_state(TrainingStates.menu)

    user_data: dict[str, int | dict] = await state.get_data()
    changed_exercise_data = user_data.get('changed_exercise_data')
    date = changed_exercise_data.get('date')
    training_id = changed_exercise_data.get('id')

    async with BotApiClient() as api_client:
        await api_client.delete_training(training_id)

    exercise_data = user_data.get('exercise_data')
    exercise_data['date'] = date

    await state.update_data(changed_exercise_data=None)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(is_back_to_menu=True),
    )

