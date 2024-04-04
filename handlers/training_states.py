from aiogram.fsm.state import StatesGroup, State



class TrainingStates(StatesGroup):
    select_date             = State()   # выбор даты
    select_exercise         = State()   # выбор упражнения
    select_weight           = State()   # выбор веса
    select_repetitions      = State()   # выбор повторений
    acept_addition          = State()   # подтверждение добавления упражнения/подхода
    menu                    = State()   # главное меню
    add_comment             = State()   # добавление комментария
    edti_mode               = State()
    edit_choose_exercise    = State()   
    edit_choose_set         = State()
    edit_choose_mode        = State()