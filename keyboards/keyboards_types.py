from enum import Enum



class PaginationAction(Enum):
    """
    Состояния пагинации
    """
    
    NEXT = 'next'
    PREV = 'prev'
    SET = 'set'