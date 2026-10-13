"""Состояния и режимы FSM-сценария тренировки."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from aiogram.fsm.state import State, StatesGroup

SetData = dict[str, int | Decimal | datetime | str]  # Тип для данных о подходе
ExerciseData = dict[str, str | int | dict[int, SetData]]  # Тип для данных об упражнении
TrainingData = dict[str, int | date | dict[int, ExerciseData]]  # Тип для данных о тренировке


class TrainingMode(Enum):
    ADD_EXERCISE = "add_exercise"
    ADD_SET = "add_set"
    EDIT_SET = "edit_set"
    EDIT_DATE = "edit_date"


class TrainingFlowStep(str, Enum):
    """JSON-friendly шаг Telegram-сценария для восстановления интерфейса.

    Значения намеренно соответствуют экранным состояниям `TrainingStates`, но
    не содержат aiogram-объекты и поэтому могут храниться в FSM draft.
    """

    SELECT_DATE = "select_date"
    CHANGE_DATE_ACCEPT = "change_date_accept"
    SELECT_EXERCISE = "select_exercise"
    SET_FORM = "set_form"
    MENU = "menu"
    ADD_COMMENT = "add_comment"
    EDIT_MENU = "edit_menu"
    EDIT_SELECT_EXERCISE = "edit_select_exercise"
    EDIT_SELECT_SET = "edit_select_set"
    EDIT_DELETE = "edit_delete"
    RESUME_PROMPT = "resume_prompt"
    RESULT = "result"


class TrainingStates(StatesGroup):
    select_date = State()  # выбор даты
    change_date_accept = State()  # изменение даты
    select_exercise = State()  # выбор упражнения
    set_form = State()  # единая форма создания и редактирования подходов
    menu = State()  # главное меню
    add_comment = State()  # добавление комментария
    edit_menu = State()  # режим редактирования
    edit_select_exercise = State()  # выбор упражнения для редактирования
    edit_select_set = State()  # выбор подхода
    edit_delete = State()  # удаление упражнения/подхода
    resume_prompt = State()  # восстановление незавершенного черновика
    result = State()  # сохраненная тренировка, ожидающая показа результата


_STATE_TO_FLOW_STEP = {
    TrainingStates.select_date.state: TrainingFlowStep.SELECT_DATE,
    TrainingStates.change_date_accept.state: TrainingFlowStep.CHANGE_DATE_ACCEPT,
    TrainingStates.select_exercise.state: TrainingFlowStep.SELECT_EXERCISE,
    TrainingStates.set_form.state: TrainingFlowStep.SET_FORM,
    TrainingStates.menu.state: TrainingFlowStep.MENU,
    TrainingStates.add_comment.state: TrainingFlowStep.ADD_COMMENT,
    TrainingStates.edit_menu.state: TrainingFlowStep.EDIT_MENU,
    TrainingStates.edit_select_exercise.state: TrainingFlowStep.EDIT_SELECT_EXERCISE,
    TrainingStates.edit_select_set.state: TrainingFlowStep.EDIT_SELECT_SET,
    TrainingStates.edit_delete.state: TrainingFlowStep.EDIT_DELETE,
    TrainingStates.resume_prompt.state: TrainingFlowStep.RESUME_PROMPT,
    TrainingStates.result.state: TrainingFlowStep.RESULT,
}

_FLOW_STEP_TO_STATE = {
    flow_step: state_name
    for state_name, flow_step in _STATE_TO_FLOW_STEP.items()
}


def flow_step_from_state(state_name: str | None) -> TrainingFlowStep:
    """Возвращает typed-представление текущего aiogram state.

    Args:
        state_name: строковое значение из `FSMContext.get_state`.

    Returns:
        Шаг сценария, соответствующий текущему состоянию.

    Raises:
        ValueError: если состояние не относится к тренировочному сценарию.
    """
    if state_name is None or state_name not in _STATE_TO_FLOW_STEP:
        raise ValueError(f"Неизвестное состояние тренировки: {state_name}")
    return _STATE_TO_FLOW_STEP[state_name]


def state_from_flow_step(flow_step: TrainingFlowStep) -> str:
    """Возвращает строковое aiogram-состояние для восстановленного шага."""
    return _FLOW_STEP_TO_STATE[flow_step]
