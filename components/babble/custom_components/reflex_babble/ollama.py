import ollama
from .state import State, QA
from typing import Any, AsyncGenerator
import os

async def answer_question(question: str, current_chat: list[QA]) -> AsyncGenerator[str, None]:
    # Build the messages.
    messages = [
        {
            "role": "system",
            "content": "You are a friendly chatbot named Reflex. Respond in markdown.",
        }
    ]
    for qa in current_chat:
        messages.append({"role": "user", "content": qa.question})
        messages.append({"role": "assistant", "content": qa.answer})

    # Remove the last mock answer.
    messages = messages[:-1]

    # Start a new session to answer the question.
    session: list[dict[str, Any]] = ollama.chat(
        model=os.getenv("OLLAMA_MODEL", "mistral-nemo:12b-instruct-2407-q4_K_M"),
        messages=messages,
        stream=True,
    )

    # Stream the results, yielding after every word.
    for item in session:
        message = item.get('message', None)
        if not message:
            continue 
        if message['role'] != 'assistant':
            continue
        if message['content']:
            answer_text = message['content']
            yield answer_text