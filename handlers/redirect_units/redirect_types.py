from aiogram.fsm.state import StatesGroup, State

from dataclasses import dataclass


class RedirectStates(StatesGroup):
    edit_redirect_group = State()   # выбор группы


@dataclass
class RedirectGroup:
    id: int
    group_id: int
    group_name: str
    is_redirect_to_group: bool
