from ..templates import template
import reflex as rx
from reflex_babble import babble
from reflex_babble.ollama import OllamaAPI
from reflex_babble.state import QA, Chat, API, API_INSTANCES
from typing import AsyncGenerator
import uuid 

class MyChatAPI(OllamaAPI):

    def get_identifier(self) -> str:
        return 'mychatapi'

    async def save_chat(self, chat: Chat):
        return 

    async def delete_chat(self, identifier: str):
        return 

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
