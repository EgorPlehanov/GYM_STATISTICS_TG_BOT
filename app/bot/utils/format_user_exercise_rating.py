from aiogram import html
from typing import List

from app.domain.statistics.service import StatisticData



def get_prize_message(place):
    """
    Возвращает премию по месту
    """
    match place:
        case 1:
            return "🥇"
        case 2:
            return "🥈"
        case 3:
            return "🥉"
        case _:
            return "🏅"



def format_user_exercise_rating(statistics: List[StatisticData]) -> str:
    """
    Форматирует рейтинг пользователя в красивый текст сообщения.
    """    
    stats_text = ''
    cur_rank = ''
    rank_str = ''
    for i, stat in enumerate(statistics):

        rating_value = html.bold(str(stat.rating_value).rstrip('0').rstrip("."))
        rank_str += f"{get_prize_message(i + 1)} {stat.exercise_name}: {rating_value}\n"

        rank_str_name = f"{stat.rank_name} {''.join(['⭐️' for _ in range(stat.rank_level)])}"
        if rank_str_name != cur_rank:
            stats_text += html.blockquote(html.spoiler(f"{html.bold(rank_str_name)}\n{rank_str}"))
            cur_rank = rank_str_name
            rank_str = ''

    return f"📈 {html.bold(html.underline('Твои лучшие результаты:'))}\n{stats_text}"

