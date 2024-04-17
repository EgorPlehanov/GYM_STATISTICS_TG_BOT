from typing import Dict, Union



def get_current_exercise_id(
    user_data: Dict[str, Union[int, Dict]]
) -> int:
    """
    Возвращает текущее упражнение
    """
    exercise_id = None
    if user_data.get('edit_exercise_id') is not None:   # если мы редактируем упражнение
        exercise_id = user_data['edit_exercise_id']
    elif user_data.get('cur_exercise_id') is not None:  # если мы добавляем упражнение
        exercise_id = user_data['cur_exercise_id']
    elif user_data.get('exercise_id') is not None:      # текущее упражнение
        exercise_id = user_data['exercise_id']
    return exercise_id



def get_current_set_id(
    user_data: Dict[str, Union[int, Dict]],
    current_exercise_id: int = None
) -> int:
    """
    Возвращает текущий подход
    """
    set_id = None
    if user_data.get('edit_set_id') is not None:        # если мы редактируем подход
        set_id = user_data['edit_set_id']
    else:                                               # текущий подход
        exercise_data = user_data['exercise_data']      
        exercise_sets = exercise_data['exercises'].get(current_exercise_id)
        if exercise_sets is None:   # если это первый подход (упражнение еще не создано)
            set_id = 1
        else:                       # текущий подход (больше на единицу чем последний записанный)
            set_id = exercise_sets['local_set_counter'] + 1
    return set_id



def get_weight_repetitions_modes_values(
    user_data: Dict[str, Union[int, Dict]],
    is_weight: bool = False,
    is_repetitions: bool = False,
):
    """
    Возвращает значения для кнопок веса и повторений
    """
    weight_repetitions_modes = user_data.get('weight_repetitions_modes')

    exercise_id = get_current_exercise_id(user_data)

    exercise_mode = weight_repetitions_modes.get(exercise_id)
    if exercise_mode is None:   # если для этого упражнения не расчитана мода
        if is_weight and is_repetitions:
            return '', ''
        else:
            return ''
        
    max_exercise_order = exercise_mode.get('max_exercise_order')
    sets_modes = exercise_mode.get('sets_modes')

    set_id = get_current_set_id(user_data, exercise_id)
    
    if set_id > max_exercise_order: # если для этого подхода не расчитана мода
        set_modes = sets_modes[max_exercise_order]
    else:
        set_modes = sets_modes[set_id]

    weight = set_modes.get('weight_mode', '')
    repetitions = set_modes.get('repetitions_mode', '')

    if is_weight and is_repetitions:
        return str(weight), str(repetitions)
    if is_weight:
        return str(weight)
    if is_repetitions:
        return str(repetitions)