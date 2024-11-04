from ..templates import template
import reflex as rx
from reflex.state import BaseState
from reflex_babble import babble
from reflex_babble.client import GenericClient
from reflex_babble.state import Chat, ChatMessage
from typing import AsyncGenerator, Any, Type
from rxconfig import config
from reflex_babble.state import ChatStateMixin
from ..components.authn import State as AuthState
from ..components.authn import httpx_auth, decode_token
import httpx
import os
import functools
import jwt
import traceback

class ChatClient(GenericClient):

    access_token: str = rx.Cookie(name='access_token')
    id_token: str = rx.Cookie(name='id_token')
    token_type: str = rx.Cookie(name='token_type')

    endpoint: str = f'{config.api_url}/chat/completion'
    model: str = 'mistral-nemo:12b-instruct-2407-q4_K_M'

    async def httpx_connection_options(self) -> dict[str, Any]:
        opts = await super().httpx_connection_options()
        opts['timeout'] = httpx.Timeout(10)
        if self.id_token:
            opts['auth'] = httpx_auth(self.token_type, self.id_token)
        return opts

@template(route="/chat", title="Chat")
def chat_page() -> rx.Component:
    """The table page.

    Returns:
        The UI for the table page.
    """
    return rx.vstack(
        rx.heading("Chat", size="5"),
        babble(state_cls=ChatClient, width="100%"),
        spacing="8",
        width="100%",
    )
