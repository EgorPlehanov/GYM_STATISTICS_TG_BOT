from typing import Dict, Union
from datetime import datetime


def initialize_exercise_data() -> Dict[str, Union[int, Dict]]:
    """
    Инициализирует данные о тренировке
    """
    return {
        "global_set_counter": 7,
        "exercises": {
            3: {
                "exercise_name": "Планка",
                "local_set_counter": 5,
                "sets": {
                    1: {
                        "set_number": 1,
                        "weight": 0.25,
                        "repetitions": 5,
                        "time": None,
                    },
                    2: {
                        "set_number": 2,
                        "weight": 0.25,
                        "repetitions": 5,
                        "time": None,
                    },
                    3: {
                        "set_number": 3,
                        "weight": 0.25,
                        "repetitions": 5,
                        "time": None,
                    },
                    4: {
                        "set_number": 7,
                        "weight": 2.0,
                        "repetitions": 14,
                        "time": None,
                    },
                    5: {
                        "set_number": 8,
                        "weight": 2.0,
                        "repetitions": 14,
                        "time": None,
                    },
                },
            },
            5: {
                "exercise_name": "Кранчи",
                "local_set_counter": 3,
                "sets": {
                    1: {
                        "set_number": 4,
                        "weight": 1.5,
                        "repetitions": 8,
                        "time": None,
                    },
                    2: {
                        "set_number": 5,
                        "weight": 2.75,
                        "repetitions": 14,
                        "time": None,
                    },
                    3: {
                        "set_number": 6,
                        "weight": 2.75,
                        "repetitions": 14,
                        "time": None,
                    },
                },
            },
        },
    }
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


def update_weight(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    new_weight: int,
    set_number: int = None,
) -> None:
    """
    Обновляет вес
    """
    if set_number is None:
        set_number = exercise_data["exercises"][exercise_id]["local_set_counter"] - 1
    exercise_data["exercises"][exercise_id]["sets"][set_number]["weight"] = new_weight


def update_repetitions(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    new_repetitions: int,
    set_number: int = None,
) -> None:
    """
    Обновляет количество повторений
    """
    if set_number is None:
        set_number = exercise_data["exercises"][exercise_id]["local_set_counter"] - 1
    exercise_data["exercises"][exercise_id]["sets"][set_number][
        "repetitions"
    ] = new_repetitions


def update_time(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    new_time: str,
    set_number: int = None,
) -> None:
    """
    Обновляет время выполнения упражнения
    """
    if set_number is None:
        set_number = exercise_data["exercises"][exercise_id]["local_set_counter"] - 1
    exercise_data["exercises"][exercise_id]["sets"][set_number]["time"] = new_time


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
    # if not exercise_data['exercises'][exercise_id]['sets']:
    #     del exercise_data['exercises'][exercise_id]
