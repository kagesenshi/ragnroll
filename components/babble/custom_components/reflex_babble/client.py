import requests

from reflex_babble.state import Model
from .state import ChatStateMixin, Chat, ChatMessage
from typing import Any, AsyncGenerator, Optional
from .settings import settings
import os
import httpx
import json
import reflex as rx
from rxconfig import config
import abc 

class GenericClient(ChatStateMixin, mixin=True):

    base_endpoint: str = f'{config.api_url}/chat/v1'
    model_endpoint: str = f'{config.api_url}/model/v1/models'

    @rx.var
    def completion_endpoint(self) -> str:
        return f'{self.base_endpoint}/completions'

    @rx.var
    def session_endpoint(self) -> str:
        return f'{self.base_endpoint}/session'

    @rx.var
    def recent_endpoint(self) -> str:
        return f'{self.base_endpoint}/recent'
    
    @rx.var
    def agent_endpoint(self) -> str:
        return f'{self.base_endpoint}/agents'
    
    async def httpx_connection_options(self) -> dict[str, Any]:
        return {}
    
    async def generate_title(self, question: str, model: str, default: str = "New chat") -> str:
        messages = [
            { "role": "user", "content": (
                f"Summarize the following question into a title with less than 10 words. "
                f"Answer directly. NEVER wrap your answer with quote nor double quote. "
                f"Only provide the summarized title. \n" 
                f"#### START QUESTION ##### \n"
                f"{question}\n"
                f"#### END QUESTION #####")},
            { "role" : "assistant", "content": ""}
        ]

        conn_opts = await self.httpx_connection_options()
        async with httpx.AsyncClient(**conn_opts) as client:
            resp: httpx.Response = await client.post(self.completion_endpoint,json={
                'model': model,
                'messages': messages
            })
            result: dict = resp.json()
        message = result.get("message", None)
        if message:
            if not message:
                return default
            if message["role"] != "assistant":
                return default
            if message["content"]:
                return message["content"]
        return default
    
    async def process_chat(self, chat: Chat, model: str) -> AsyncGenerator[str, None]:
        # Build the messages.
        messages = [
            {
                "role": "system",
                "content": "You are a friendly chatbot named Reflex. Respond in markdown.",
            },
        ]
        
        for msg in chat.history:
            messages.append({"role": msg.role, "content": msg.message})
    
        # Remove the last mock answer.
        messages = messages[:-1]
    
        # Start a new session to answer the question.
        async with self:
            conn_opts = await self.httpx_connection_options()
        async with httpx.AsyncClient(**conn_opts) as client:
            async with client.stream('POST', self.completion_endpoint, json={
                'model': model,
                'messages': messages,
                'stream': True
            }) as resp:
                if resp.status_code != 200:
                    raise Exception(f"{resp.status_code}")
                
                async for line in resp.aiter_lines():
                    item: dict = json.loads(line)
                    if item is None:
                        continue
                    message = item.get('message', None)
                    if not message:
                        continue 
                    if message['role'] != 'assistant':
                        continue
                    if message['content']:
                        answer_text = message['content']
                        yield answer_text

    async def save_chat(self, chat: Chat):
        conn_opts = await self.httpx_connection_options()
        async with httpx.AsyncClient(**conn_opts) as client:
            resp = await client.put(f'{self.session_endpoint}/{chat.identifier}',
                json={
                    'identifier': chat.identifier,
                    'title': chat.title,
                    'timestamp': chat.timestamp.isoformat(),
                    'history': [{
                        'identifier': r.identifier,
                        'timestamp': r.timestamp.isoformat(),
                        'role': r.role,
                        'message': r.message,
                        'model': r.model
                    } for r in chat.history]
                })
        return 
    
    async def load_chats(self) -> list[Chat]:
        conn_opts = await self.httpx_connection_options()
        async with httpx.AsyncClient(**conn_opts) as client:
            resp = await client.get(f'{self.recent_endpoint}')
            if resp.status_code != 200:
                print(resp.status_code)
                return []
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
                                message=m['message'],
                                model=m['model']) 
                    for m in r['history']                   
                ]
            ) for r in result['data']
        ]

    async def delete_chat(self, identifier: str):
        conn_opts = await self.httpx_connection_options()
        async with httpx.AsyncClient(**conn_opts) as client:
            resp = await client.delete(f'{self.session_endpoint}/{identifier}')
            if not resp.status_code == 200:
                raise AssertionError(f"Failed to delete chat {identifier}. Error code: {resp.status_code}")
        return 
    
    
    async def load_models(self) -> list[Model]:
        conn_opts = await self.httpx_connection_options()
        async with httpx.AsyncClient(**conn_opts) as client:
            resp = await client.get(f'{self.model_endpoint}')
            if resp.status_code != 200:
                return []
            data = resp.json()
        result = [
            Model(title=r['title'], name=r['name']) for r in data['data']
        ]
        return result
