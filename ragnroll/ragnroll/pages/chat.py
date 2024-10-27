from ..templates import template
import reflex as rx
from reflex_babble import babble
from reflex_babble.client.ollama import OllamaClient
from reflex_babble.client.openai import OpenAIClient
from reflex_babble.client.generic import GenericClient
from reflex_babble.state import QA, Chat, API, API_INSTANCES
from typing import AsyncGenerator
from rxconfig import config
import os

class ChatClient(GenericClient):

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
        babble(api=ChatClient(endpoint=f'{config.api_url}/chat', model=os.environ['OLLAMA_MODEL']), width="100%"),
        spacing="8",
        width="100%",
    )
