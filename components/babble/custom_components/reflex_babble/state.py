import os
import reflex as rx
from openai import OpenAI
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from typing import Callable, AsyncGenerator, Any, TypedDict
from .settings import settings 
from .api import API, API_INSTANCES

class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str


DEFAULT_CHATS = {
    "Intros": [],
}

def render_markdown(text: str) -> str:
    return markdown.markdown(text, extensions=[CodeHiliteExtension(linenums=False), FencedCodeExtension()])

class State(rx.State):
    """The app state."""

    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, list[QA]] = DEFAULT_CHATS

    # The current chat name.
    current_chat = "Intros"

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    # The name of the new chat.
    new_chat_name: str = ""

    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]

    def set_chat(self, chat_name: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        self.current_chat = chat_name

    @rx.var
    def rendered_current_chat(self) -> list[QA]:
        res = []
        for c in self.chats[self.current_chat]:
            res.append(QA(question=render_markdown(c.question), 
                     answer=render_markdown(c.answer)))
        return res

    @rx.var
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list(self.chats.keys())

    async def process_question(self, api_id: str, form_data: dict[str, str]):
        # Get the question from the form
        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return

        async for value in self._process_question(api_id, question):
            yield value


    async def _process_question(self, api_id: str, question: str):
        """Get the response from the API.
    
        Args:
            form_data: A dict with the current question.
        """
    
        # Add the question to the list of questions.
        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)
    
        # Clear the input and start the processing.
        self.processing = True
        yield
    
        # Stream the results, yielding after every word.
        async for answer_text in API_INSTANCES[api_id].answer_question(question, self.chats[self.current_chat]):
            # Ensure answer_text is not None before concatenation
            if answer_text is not None:
                self.chats[self.current_chat][-1].answer += answer_text
            else:
                # Handle the case where answer_text is None, perhaps log it or assign a default value
                # For example, assigning an empty string if answer_text is None
                answer_text = ""
                self.chats[self.current_chat][-1].answer += answer_text
            self.chats = self.chats
            yield
    