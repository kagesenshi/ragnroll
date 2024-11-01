from ..templates import template
import reflex as rx
from reflex_babble import babble
from reflex_babble.client.ollama import OllamaClient
from reflex_babble.client.openai import OpenAIClient
from reflex_babble.client.generic import GenericClient
from reflex_babble.state import Chat, API, API_INSTANCES, ChatMessage
from typing import AsyncGenerator, Any
from rxconfig import config
from reflex_babble.state import State
from ..components.authn import State as AuthState
from ..components.authn import httpx_auth
import httpx
import os

class ChatClient(GenericClient):

    def get_identifier(self) -> str:
        return 'ragnroll-chat'
    
    async def httpx_connection_options(self, state: State) -> dict[str, Any]:
        auth: AuthState = await state.get_state(AuthState)
        opts = await super().httpx_connection_options(state)
        opts['timeout'] = httpx.Timeout(10)
        opts['auth'] = httpx_auth(auth.token_type, auth.id_token)
        return opts

    async def save_chat(self, state: State, chat: Chat):
        auth: AuthState = await state.get_state(AuthState)
        if not auth.logged_in:
            return []
        conn_opts = await self.httpx_connection_options(state)
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
    
    async def load_chats(self, state: State) -> list[Chat]:
        auth: AuthState = await state.get_state(AuthState)
        if not auth.logged_in:
            return []
        conn_opts = await self.httpx_connection_options(state)
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

    async def delete_chat(self, state: State, identifier: str):
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
        babble(api=ChatClient(endpoint=f'{config.api_url}/chat/completion', model=os.environ['OLLAMA_MODEL']), width="100%"),
        spacing="8",
        width="100%",
    )
