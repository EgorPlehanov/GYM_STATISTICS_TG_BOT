from typing import List

from db.queries import statistic



def get_prize_message(place):
    """
    Возвращает премию по месту
    """
    match place:
        case 1:
            return "🥇 "
        case 2:
            return "🥈 "
        case 3:
            return "🥉 "
        case _:
            return "🏅"



def format_user_exercise_rating(statistics: List[statistic]) -> str:
    """
    Форматирует рейтинг пользователя в красивый текст сообщения.
    """
    stats_text = f"📈 Твоя статистика:\n"

    if len(statistics) == 0:
        return "🏆 Добавляй тренировки и тут будут появляться твои лучшие результаты!"

    cur_rank = ''
    for i, stat in enumerate(statistics):
        rank_str = f"{stat.rank_name} {''.join(['⭐️' for _ in range(stat.rank_level)])}"

        if rank_str != cur_rank:
            stats_text += f"\n{rank_str}\n"
            cur_rank = rank_str

        stats_text += f"{get_prize_message(i + 1)} {stat.exercise_name}: {stat.rating_value}\n"

    return stats_text