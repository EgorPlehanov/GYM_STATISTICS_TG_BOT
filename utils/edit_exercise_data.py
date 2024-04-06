from typing import Dict, Union
import datetime



def initialize_exercise_data() -> Dict[str, Union[int, Dict]]:
    """
    Инициализирует данные о тренировке
    """
    return {'global_set_counter': 7, 'exercises': {
        3: {'exercise_name': 'Планка', 'local_set_counter': 5, 'sets': {
            1: {'set_number': 1, 'weight': 0.25, 'repetitions': 1, 'time': datetime.datetime(2024, 4, 5, 2, 59, 0, 633563)},
            2: {'set_number': 2, 'weight': 0.25, 'repetitions': 5, 'time': datetime.datetime(2024, 4, 5, 2, 59, 10, 648734)},
            3: {'set_number': 3, 'weight': 2.5, 'repetitions': 11, 'time': datetime.datetime(2024, 4, 5, 2, 59, 21, 484174)},
            4: {'set_number': 6, 'weight': 2.0, 'repetitions': 14, 'time': datetime.datetime(2024, 4, 5, 3, 0, 2, 158622)},
            5: {'set_number': 7, 'weight': 2.0, 'repetitions': 14, 'time': datetime.datetime(2024, 4, 5, 3, 0, 2, 158622)},
            6: {'set_number': 8, 'weight': 2.0, 'repetitions': 14, 'time': datetime.datetime(2024, 4, 5, 3, 0, 2, 158622)}}},

        5: {'exercise_name': '1 Кранчи', 'local_set_counter': 3, 'sets': {
            1: {'set_number': 4, 'weight': 1.5, 'repetitions': 8, 'time': datetime.datetime(2024, 4, 5, 2, 59, 36, 699876)},
            2: {'set_number': 5, 'weight': 2.75, 'repetitions': 14, 'time': datetime.datetime(2024, 4, 5, 2, 59, 48, 363042)}}},
        
        6: {'exercise_name': '2 Кранчи', 'local_set_counter': 3, 'sets': {
            1: {'set_number': 9, 'weight': 1.5, 'repetitions': 8, 'time': datetime.datetime(2024, 4, 5, 2, 59, 36, 699876)},
            2: {'set_number': 10, 'weight': 2.75, 'repetitions': 14, 'time': datetime.datetime(2024, 4, 5, 2, 59, 48, 363042)}}},
        
        7: {'exercise_name': '3 Кранчи', 'local_set_counter': 3, 'sets': {
            1: {'set_number': 10, 'weight': 1.5, 'repetitions': 8, 'time': datetime.datetime(2024, 4, 5, 2, 59, 36, 699876)},
            2: {'set_number': 11, 'weight': 2.75, 'repetitions': 14, 'time': datetime.datetime(2024, 4, 5, 2, 59, 48, 363042)}}},
        
        8: {'exercise_name': '4 Кранчи', 'local_set_counter': 3, 'sets': {
            1: {'set_number': 13, 'weight': 1.5, 'repetitions': 8, 'time': datetime.datetime(2024, 4, 5, 2, 59, 36, 699876)},
            2: {'set_number': 14, 'weight': 2.75, 'repetitions': 14, 'time': datetime.datetime(2024, 4, 5, 2, 59, 48, 363042)}}},
        
        9: {'exercise_name': '5 Кранчи', 'local_set_counter': 3, 'sets': {
            1: {'set_number': 12, 'weight': 1.5, 'repetitions': 8, 'time': datetime.datetime(2024, 4, 5, 2, 59, 36, 699876)},
            2: {'set_number': 15, 'weight': 2.75, 'repetitions': 14, 'time': datetime.datetime(2024, 4, 5, 2, 59, 48, 363042)}}},
    }}
    return {"global_set_counter": 1, "exercises": {}}



def add_exercise(
    exercise_data: Dict[str, Union[int, Dict]], exercise_id: str, exercise_name: str
) -> None:
    """
    Добавляет упражнение к тренировке
    """
    if exercise_id in exercise_data["exercises"]:
        return
    exercise_data["exercises"][exercise_id] = {
        "exercise_name": exercise_name,
        "local_set_counter": 1,
        "sets": {},
    }



def add_set(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    weight: int = None,
    repetitions: int = None,
    time: str = None,
) -> None:
    """
    Добавляет подход к упражнению
    """
    set_number = exercise_data["exercises"][exercise_id]["local_set_counter"]

    exercise_data["exercises"][exercise_id]["sets"][set_number] = {
        "set_number": exercise_data["global_set_counter"],
        "weight": weight,
        "repetitions": repetitions,
        "time": time,
    }

    exercise_data["exercises"][exercise_id]["local_set_counter"] += 1
    exercise_data["global_set_counter"] += 1



def update_set(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: int,
    set_id: int,
    new_weight: int = None,
    new_repetitions: int = None,
    new_time: datetime = None,
) -> bool:
    """
    Обновляет вес, количество повторений, и время выполнения упражнения
    """
    if new_weight is None and new_repetitions is None and new_time is None:
        return False
    
    if (
        exercise_id not in exercise_data["exercises"]
        or set_id not in exercise_data["exercises"][exercise_id]["sets"]
    ):
        return False

    updated_flag = False
    set_data = exercise_data["exercises"][exercise_id]["sets"][set_id]

    if new_weight is not None and new_weight != set_data["weight"]:
        set_data["weight"] = new_weight
        updated_flag = True

    if new_repetitions is not None and new_repetitions != set_data["repetitions"]:
        set_data["repetitions"] = new_repetitions
        updated_flag = True

    if new_time is not None and new_time != set_data["time"]:
        set_data["time"] = new_time
        updated_flag = True

    return updated_flag



def delete_exercise(
    exercise_data: Dict[str, Union[int, Dict]], exercise_id: str
) -> None:
    """
    Удаляет упражнение со всеми подходами
    """
    del exercise_data["exercises"][exercise_id]



def delete_set(
    exercise_data: Dict[str, Union[int, Dict]], exercise_id: str, set_number: str
) -> None:
    """
    Удаляет подход
    """
    del exercise_data["exercises"][exercise_id]["sets"][set_number]
    # Удаляет упражнение, если нет ни одного подхода
    if not exercise_data['exercises'][exercise_id]['sets']:
        del exercise_data['exercises'][exercise_id]



def delete_all_exercises(exercise_data: Dict[str, Union[int, Dict]]) -> None:
    """
    Удаляет все упражнения
    """
    exercise_data["exercises"] = {}



def delete_all_exercise_sets(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    is_sets_only: bool = False,
) -> None:
    """
    Удаляет все подходы упражнения
    """
    if is_sets_only:
        del exercise_data["exercises"][exercise_id]["sets"]
    else:
        del exercise_data["exercises"][exercise_id]