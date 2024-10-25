import ollama
from .state import State, QA, Chat, API
from typing import Any, AsyncGenerator
from .settings import settings
import os


class OllamaAPI(API):

    async def generate_title(self, question: str, default: str = "New chat") -> str:
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

        result: dict[str, Any] = await ollama.AsyncClient().chat(model=settings.OLLAMA_MODEL, messages=messages)
        message = result.get("message", None)
        if message:
            if not message:
                return default
            if message["role"] != "assistant":
                return default
            if message["content"]:
                return message["content"]
        return default
    
    async def process_chat(self, chat: Chat) -> AsyncGenerator[str, None]:
        # Build the messages.
        messages = [
            {
                "role": "system",
                "content": "You are a friendly chatbot named Reflex. Respond in markdown.",
            },
        ]
        
        for qa in chat.history:
            messages.append({"role": "user", "content": qa.question})
            messages.append({"role": "assistant", "content": qa.answer})
    
        # Remove the last mock answer.
        messages = messages[:-1]
    
        # Start a new session to answer the question.
        session: list[dict[str, Any]] = await ollama.AsyncClient().chat(
            model=settings.OLLAMA_MODEL,
            messages=messages,
            stream=True,
        )
    
        # Stream the results, yielding after every word.
        async for item in session:
            message = item.get('message', None)
            if not message:
                continue 
            if message['role'] != 'assistant':
                continue
            if message['content']:
                answer_text = message['content']
                yield answer_text