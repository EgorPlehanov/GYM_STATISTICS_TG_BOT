from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from typing import Dict, Union



class StateAttributeNotNoneFilter(BaseFilter):
    """
    Проверяет что атрибут состояния не равен None
    """
    def __init__(self, attribute_name: str):
        self.attribute_name = attribute_name


    async def __call__(self, message: Message, state: FSMContext) -> bool:

        user_data: Dict[str, Union[int, Dict]] = await state.get_data()

        return user_data.get(self.attribute_name) is not None
        

