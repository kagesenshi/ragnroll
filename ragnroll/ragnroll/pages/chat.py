from ..templates import template
import reflex as rx
from reflex_babble import babble
from reflex_babble.api import API
from reflex_babble.ollama import answer_question
from reflex_babble.state import QA
from typing import AsyncGenerator

class MyChatAPI(API):

    def get_identifier(self) -> str:
        return 'mychatapi'

    async def answer_question(self, question: str, current_chat: list[QA]) -> AsyncGenerator[str, None]:
        async for i in answer_question(question, current_chat):
            yield i

@template(route="/chat", title="Chat")
def chat_page() -> rx.Component:
    """The table page.

    Returns:
        The UI for the table page.
    """
    return rx.vstack(
        rx.heading("Chat", size="5"),
        babble(api=MyChatAPI(), width="100%"),
        spacing="8",
        width="100%",
    )
