from .state import State, QA
import os
from openai import OpenAI
from .settings import settings

async def openai_process_question(state: type[State], question: str):
    """Get the response from the API.

    Args:
        form_data: A dict with the current question.
    """

    # Add the question to the list of questions.
    qa = QA(question=question, answer="")
    state.chats[state.current_chat].append(qa)

    # Clear the input and start the processing.
    state.processing = True
    yield

    # Build the messages.
    messages = [
        {
            "role": "system",
            "content": "You are a friendly chatbot named Reflex. Respond in markdown.",
        }
    ]
    for qa in state.chats[state.current_chat]:
        messages.append({"role": "user", "content": qa.question})
        messages.append({"role": "assistant", "content": qa.answer})

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
            if answer_text is not None:
                state.chats[state.current_chat][-1].answer += answer_text
            else:
                # Handle the case where answer_text is None, perhaps log it or assign a default value
                # For example, assigning an empty string if answer_text is None
                answer_text = ""
                state.chats[state.current_chat][-1].answer += answer_text
            state.chats = state.chats
            yield

    # Toggle the processing flag.
    state.processing = False
    
