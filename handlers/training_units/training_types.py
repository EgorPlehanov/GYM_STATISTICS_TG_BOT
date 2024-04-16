from aiogram.fsm.state import StatesGroup, State

from typing import Dict, Union
from datetime import datetime
from enum import Enum
from collections import namedtuple



SetData = Dict[str, Union[int, float, datetime, str]]  # Тип для данных о подходе
ExerciseData = Dict[str, Union[str, int, Dict[int, SetData]]]  # Тип для данных об упражнении
TrainingData = Dict[str, Union[int, Dict[int, ExerciseData]]]  # Тип для данных о тренировке



class TrainingMode(Enum):
    ADD_EXERCISE = "add_exercise"
    ADD_SET = "add_set"
    EDIT_SET = "edit_set"
    EDIT_DATE = "edit_date" 



class TrainingStates(StatesGroup):
    select_date             = State()   # выбор даты
    change_date_acept       = State()   # изменение даты
    select_exercise         = State()   # выбор упражнения
    select_weight           = State()   # выбор веса
    select_repetitions      = State()   # выбор повторений
    acept_addition          = State()   # подтверждение добавления упражнения/подхода
    select_sets_count       = State()   # выбор количества подходов
    menu                    = State()   # главное меню
    add_comment             = State()   # добавление комментария
    edit_menu               = State()   # режим редактирования
    edit_select_exercise    = State()   # выбор упражнения для редактирования
    edit_select_set         = State()   # выбор подхода для редактирования
    edit_delete             = State()   # удаление упражнения/подхода



Button = namedtuple("back_button", ["text", "callback_data"])



exercise_button_by_mode = {
    TrainingMode.ADD_EXERCISE: Button("Упражнение", "to_exercise"),
    TrainingMode.ADD_SET: Button("Меню", "to_menu"),
}



weight_back_button_by_mode = {
    TrainingMode.ADD_EXERCISE: Button("Упражнение", "to_exercise"),
    TrainingMode.ADD_SET: Button("Меню", "to_menu"),
    TrainingMode.EDIT_SET: Button("Подход", "to_edit_menu_set"),
}



acept_button_by_mode = {
    TrainingMode.ADD_EXERCISE: Button("Добавить", "acept_addition"),
    TrainingMode.ADD_SET: Button("Добавить", "acept_addition"),
    TrainingMode.EDIT_SET: Button("Подтвердить изменения", "acept_edit"),
}