from ..templates import template
import reflex as rx
from reflex.state import BaseState
from reflex_babble import babble
from reflex_babble.client import GenericClient
from reflex_babble.state import Chat, ChatMessage
from typing import AsyncGenerator, Any, Type
from rxconfig import config
from reflex.utils.exceptions import ImmutableStateError
from reflex_babble.state import ChatStateMixin
from ..components.authn import AuthState
from ..components.authn import httpx_auth, decode_token
import httpx
import os
import functools
import jwt
import traceback

class ChatClient(GenericClient):

    async def httpx_connection_options(self) -> dict[str, Any]:
        opts = await super().httpx_connection_options()
        opts['timeout'] = httpx.Timeout(10)
        auth: AuthState = await self.get_state(AuthState)
        if auth.id_token:
            opts['auth'] = httpx_auth(auth.token_type, auth.id_token)
        return opts

@template(route="/chat", title="Chat")
def chat_page() -> rx.Component:
    """The table page.

    Returns:
        The UI for the table page.
    """
    return rx.vstack(
        rx.heading("Chat", size="5"),
        babble(state_cls=ChatClient, disclaimer="This bot may return factually incorrect or misleading responses. Use with discretion", width="100%"),
        spacing="8",
        width="100%",
    )
