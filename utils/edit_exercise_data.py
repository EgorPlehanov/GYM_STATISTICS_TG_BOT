from typing import Dict, Union
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from db.queries import (
    check_training_exists_for_user_and_date,
    get_training_data_by_date_and_user
)



async def initialize_exercise_data(
    session: AsyncSession,
    user_id: int,
    date: datetime
) -> tuple[Dict[str, Union[int, Dict]], bool]:
    """
    Инициализирует данные о тренировке
    """
    is_exists = await check_training_exists_for_user_and_date(session, user_id, date)
    if is_exists:
        init_exercise_data = await get_training_data_by_date_and_user(session, user_id, date)
    else:
        init_exercise_data =  {
            "id": None,
            "user_id": user_id,
            "date": date,
            "comment": None,
            "global_set_counter": 0,
            "exercises": {}
        }
    return init_exercise_data, is_exists



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
        "local_set_counter": 0,
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
    exercise_data["exercises"][exercise_id]["local_set_counter"] += 1
    exercise_data["global_set_counter"] += 1

    set_number = exercise_data["exercises"][exercise_id]["local_set_counter"]

    exercise_data["exercises"][exercise_id]["sets"][set_number] = {
        "set_number": exercise_data["global_set_counter"],
        "weight": weight,
        "repetitions": repetitions,
        "time": time,
    }




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



def delete_set(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    set_number: str
) -> None:
    """
    Удаляет подход
    """
    del exercise_data["exercises"][exercise_id]["sets"][set_number]
    # Удаляет упражнение, если нет ни одного подхода
    if not exercise_data['exercises'][exercise_id]['sets']:
        del exercise_data['exercises'][exercise_id]
    update_indexes_exercise_data(exercise_data)



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
    update_indexes_exercise_data(exercise_data)



def delete_exercise(
    exercise_data: Dict[str, Union[int, Dict]], exercise_id: str
) -> None:
    """
    Удаляет упражнение со всеми подходами
    """
    del exercise_data["exercises"][exercise_id]
    update_indexes_exercise_data(exercise_data)



def delete_all_exercises(exercise_data: Dict[str, Union[int, Dict]]) -> None:
    """
    Удаляет все упражнения
    """
    exercise_data["exercises"] = {}
    update_indexes_exercise_data(exercise_data)



def update_indexes_exercise_data(
    exercise_data: Dict[str, Union[int, Dict]],
) -> None:
    """
    Обновляет индексы подходов
    """
    all_sets = []
    for exercise in exercise_data["exercises"].values():
        all_sets.extend(list(exercise["sets"].values()))

        local_set_counter = 0
        sets_keys = list(exercise["sets"].keys())
        for set_idx in sets_keys:
            local_set_counter += 1
            if set_idx != local_set_counter:
                exercise["sets"][local_set_counter] = exercise["sets"].pop(set_idx)

        exercise["local_set_counter"] = local_set_counter
    
    all_sets_sorted = sorted(all_sets, key=lambda x: x["set_number"])
    for idx in range(len(all_sets_sorted)):
        all_sets_sorted[idx]["set_number"] = idx + 1

    exercise_data["global_set_counter"] = len(all_sets_sorted)