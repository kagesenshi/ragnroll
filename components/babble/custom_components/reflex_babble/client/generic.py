import requests
from ..state import State, Chat, ChatMessage, API
from typing import Any, AsyncGenerator, Optional
from ..settings import settings
import os
import httpx
import json


class GenericClient(API):

    def __init__(self, endpoint: str, model: str, stream_endpoint: Optional[str] = None):
        self.endpoint = endpoint
        self.stream_endpoint = stream_endpoint or endpoint
        self.model = model

    async def generate_title(self, state: State, question: str, default: str = "New chat") -> str:
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

        conn_opts = await self.httpx_connection_options(state)
        async with httpx.AsyncClient(**conn_opts) as client:
            resp: httpx.Response = await client.post(self.endpoint,json={
                'model': self.model,
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
    
    async def process_chat(self, state: State, chat: Chat) -> AsyncGenerator[str, None]:
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
        conn_opts = await self.httpx_connection_options(state)
        async with httpx.AsyncClient(**conn_opts) as client:
            async with client.stream('POST', self.endpoint, json={
                'model': self.model,
                'messages': messages,
                'stream': True
            }) as resp:
                
                async for line in resp.aiter_lines():
                    item: dict = json.loads(line)
                    message = item.get('message', None)
                    if not message:
                        continue 
                    if message['role'] != 'assistant':
                        continue
                    if message['content']:
                        answer_text = message['content']
                        yield answer_text