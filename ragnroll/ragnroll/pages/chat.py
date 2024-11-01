from ..templates import template
import reflex as rx
from reflex.state import BaseState
from reflex_babble import babble
from reflex_babble.client.ollama import OllamaClient
from reflex_babble.client.openai import OpenAIClient
from reflex_babble.client.generic import GenericClient
from reflex_babble.state import Chat, ChatMessage
from typing import AsyncGenerator, Any, Type
from rxconfig import config
from reflex_babble.state import ChatStateMixin
from ..components.authn import State as AuthState
from ..components.authn import httpx_auth
import httpx
import os
import functools

class ChatClient(GenericClient):

    def get_identifier(self) -> str:
        return 'ragnroll-chat'
    
    endpoint: str = f'{config.api_url}/chat/completion'
    model: str = 'mistral-nemo:12b-instruct-2407-q4_K_M'

    async def httpx_connection_options(self) -> dict[str, Any]:
        auth: AuthState = await self.get_state(AuthState)
        opts = await super().httpx_connection_options()
        opts['timeout'] = httpx.Timeout(10)
        opts['auth'] = httpx_auth(auth.token_type, auth.id_token)
        return opts

    async def save_chat(self, chat: Chat):
        auth: AuthState = await self.get_state(AuthState)
        if not auth.logged_in:
            return []
        conn_opts = await self.httpx_connection_options()
        async with httpx.AsyncClient(**conn_opts) as client:
            resp = await client.put(f'{config.api_url}/chat/session/{chat.identifier}',
                json={
                    'identifier': chat.identifier,
                    'title': chat.title,
                    'timestamp': chat.timestamp.isoformat(),
                    'history': [{
                        'identifier': r.identifier,
                        'timestamp': r.timestamp.isoformat(),
                        'role': r.role,
                        'message': r.message
                    } for r in chat.history]
                })
        return 
    
    async def load_chats(self) -> list[Chat]:
        auth: AuthState = await self.get_state(AuthState)
        if not auth.logged_in:
            return []
        conn_opts = await self.httpx_connection_options()
        async with httpx.AsyncClient(**conn_opts) as client:
            resp = await client.get(f'{config.api_url}/chat/recent')
            result = resp.json()
        return [
            Chat(
                identifier=r['identifier'],
                timestamp=r['timestamp'],
                title=r['title'],
                history=[
                    ChatMessage(identifier=m['identifier'],
                                timestamp=m['timestamp'],
                                role=m['role'],
                                message=m['message']) 
                    for m in r['history']                   
                ]
            ) for r in result['data']
        ]

    async def delete_chat(self, identifier: str):
        print("Deleting chat...")
        return 

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


class MixinTestMixin(rx.State, mixin=True):

    async def on_mount(self):
        print('mount!')

    @classmethod
    def get_parent_state(cls) -> Type[BaseState] | None:
        return rx.State


class MixinTest(MixinTestMixin):
    pass

@template(route="/mixintest", title="Mixin Test")
def mixin_test() -> rx.Component:
    return rx.vstack(
        on_mount=MixinTest.on_mount,
    )