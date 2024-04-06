from typing import Dict



def format_set_data_to_text(set_data: Dict[str, int]) -> str:
        """
        Форматирует строку текста подхода
        """
        str_parts = []

        set_number = set_data['set_number']
        if set_number is not None:
            str_parts.append(f"{set_number})")

        time = set_data['time'].strftime('%H:%M')
        if time is not None:
            str_parts.append(f"{time} -")

        weight = str(set_data['weight']).rstrip('0').rstrip(".")
        if weight is not None:
            str_parts.append(f"{weight}")

        repetitions = set_data['repetitions']
        if repetitions is not None:
            str_parts.append(f"× {repetitions}")

        return ' '.join(str_parts)