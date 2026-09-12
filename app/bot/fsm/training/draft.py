"""Операции над текущим FSM-черновиком тренировки."""

from datetime import datetime
from typing import Any


def add_exercise(
    exercise_data: dict[str, Any], exercise_id: str, exercise_name: str
) -> None:
    """Добавляет упражнение к черновику тренировки."""
    if exercise_id in exercise_data["exercises"]:
        return
    exercise_data["exercises"][exercise_id] = {
        "exercise_name": exercise_name,
        "local_set_counter": 0,
        "sets": {},
    }



def add_set(
    exercise_data: dict[str, Any],
    exercise_id: str,
    weight: int = None,
    repetitions: int = None,
    time: str = None,
) -> None:
    """Добавляет подход к упражнению в черновике тренировки."""
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
    exercise_data: dict[str, Any],
    exercise_id: int,
    set_id: int,
    new_weight: int = None,
    new_repetitions: int = None,
    new_time: datetime = None,
) -> bool:
    """Обновляет вес, количество повторений или время выполнения подхода."""
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
    exercise_data: dict[str, Any],
    exercise_id: str,
    set_number: str
) -> None:
    """Удаляет подход из черновика тренировки."""
    del exercise_data["exercises"][exercise_id]["sets"][set_number]
    # Удаляет упражнение, если нет ни одного подхода
    if not exercise_data['exercises'][exercise_id]['sets']:
        del exercise_data['exercises'][exercise_id]
    update_indexes_exercise_data(exercise_data)



def delete_all_exercise_sets(
    exercise_data: dict[str, Any],
    exercise_id: str,
    is_sets_only: bool = False,
) -> None:
    """Удаляет все подходы упражнения из черновика тренировки."""
    if is_sets_only:
        del exercise_data["exercises"][exercise_id]["sets"]
    else:
        del exercise_data["exercises"][exercise_id]
    update_indexes_exercise_data(exercise_data)



def delete_exercise(
    exercise_data: dict[str, Any], exercise_id: str
) -> None:
    """Удаляет упражнение со всеми подходами из черновика тренировки."""
    del exercise_data["exercises"][exercise_id]
    update_indexes_exercise_data(exercise_data)



def delete_all_exercises(exercise_data: dict[str, Any]) -> None:
    """Удаляет все упражнения из черновика тренировки."""
    exercise_data["exercises"] = {}
    update_indexes_exercise_data(exercise_data)



def update_indexes_exercise_data(
    exercise_data: dict[str, Any],
) -> None:
    """Обновляет локальные и глобальные индексы подходов в черновике."""
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

