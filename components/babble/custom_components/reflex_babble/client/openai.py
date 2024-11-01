import os
from openai import OpenAI
from ..settings import settings
from ..state import State, Chat, API
from typing import Any, AsyncGenerator

class OpenAIClient(API):
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

        result = OpenAI().chat.completions.create(
            model=settings.OPENAI_MODEL, 
            messages=messages
        )

        if hasattr(result.choices[0].message, 'content'):
            answer = result.choices[0].message.content
            if answer:
                return answer 
            return default
        return default 

    async def process_chat(self, state: State, chat: Chat):
        # Build the messages.
        messages = [
            {
                "role": "system",
                "content": "You are a friendly chatbot named Reflex. Respond in markdown.",
            }
        ]

        for msg in chat.history:
            messages.append({"role": msg.role, "content": msg.message})
    
        # Remove the last mock answer.
        messages = messages[:-1]
    
        # Start a new session to answer the question.
        session = OpenAI().chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            stream=True,
        )
    
        # Stream the results, yielding after every word.
        for item in session:
            if hasattr(item.choices[0].delta, "content"):
                answer_text = item.choices[0].delta.content
                # Ensure answer_text is not None before concatenation
                if not answer_text:
                    continue
                else:
                    yield answer_text
    