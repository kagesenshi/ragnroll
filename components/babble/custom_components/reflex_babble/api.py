import reflex as rx
from typing import AsyncGenerator, TYPE_CHECKING
import abc 
if TYPE_CHECKING:
    from .state import QA

class API(abc.ABC):

    @abc.abstractmethod
    def get_identifier(self) -> str:
        raise NotImplemented

    @abc.abstractmethod
    async def answer_question(self, question: str, current_chat: list['QA']) -> AsyncGenerator[str, None]:
        raise NotImplemented

# XXX: not sure if this is good idea
API_INSTANCES: dict[str, API]={}
