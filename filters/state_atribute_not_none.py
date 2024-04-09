from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from typing import Dict, Union



class StateAtributeNotNoneFilter(BaseFilter):
    def __init__(self, atribute_name: str):
        self.atribute_name = atribute_name


    async def __call__(self, message: Message, state: FSMContext) -> bool:

        user_data: Dict[str, Union[int, Dict]] = await state.get_data()

        return user_data.get(self.atribute_name) is not None
        