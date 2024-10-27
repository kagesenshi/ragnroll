import os
import reflex as rx
from openai import OpenAI
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from typing import Callable, AsyncGenerator, Any, TypedDict, Optional
from .settings import settings 
import abc 
from uuid_extensions import uuid7

class QA(rx.Base):
    """A question and answer pair."""

    identifier: str
    question: str
    answer: str

class Chat(rx.Base):

    identifier: str
    title: str
    history: list[QA]    


class API(abc.ABC):

    @abc.abstractmethod
    def get_identifier(self) -> str:
        raise NotImplemented

    @abc.abstractmethod
    async def generate_title(self, question: str, default: str = 'New chat') -> str:
        raise NotImplemented

    @abc.abstractmethod
    async def process_chat(self, chat: 'Chat') -> AsyncGenerator[str, None]:
        raise NotImplemented

    @abc.abstractmethod 
    async def save_chat(self, chat: 'Chat'):
        raise NotImplemented
    
    @abc.abstractmethod
    async def delete_chat(self, identifier: str):
        raise NotImplemented
    
    async def set_chat(self, chat_id: str):
        pass


# XXX: not sure if this is good idea
API_INSTANCES: dict[str, API]={}


DEFAULT_CHATS = {
    "Intros": [],
}

def render_markdown(text: str) -> str:
    return markdown.markdown(text, extensions=[CodeHiliteExtension(linenums=False), FencedCodeExtension()])

class State(rx.State):
    """The app state."""

    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, Chat] = {}

    # The current chat name.
    current_chat: Optional[str] = None

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    input_value: str = ''

    previous_key: str = ''

    multiline: bool = False

    async def new_chat(self):
        self.current_chat = None

    async def delete_chat(self, api_id: str, chat_id: str):
        """Delete the current chat."""
        api = API_INSTANCES[api_id]
        await api.delete_chat(chat_id)

        del self.chats[self.current_chat]
        self.current_chat = None

    async def set_chat(self, api_id: str, chat_id: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        api = API_INSTANCES[api_id]
        await api.set_chat(chat_id)
        self.current_chat = chat_id

    @rx.var
    def rendered_current_chat(self) -> list[QA]:
        res = []
        if self.current_chat is None:
            return []
        for c in self.chats[self.current_chat].history:
            res.append(QA(identifier=c.identifier,
                          question=render_markdown(c.question), 
                        answer=render_markdown(c.answer)))
        return res

    @rx.var
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list([c.title for c in self.chats.values()])

    async def process_question(self, api_id: str, form_data: dict[str, str]):
        # Get the question from the form

        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return
        
        if not question:
            return

        if self.multiline:
            self.multiline = False

        async for value in self._process_question(api_id, question):
            yield value


    async def _process_question(self, api_id: str, question: str, default_title: str = 'New chat'):
        """Get the response from the API.
    
        Args:
            form_data: A dict with the current question.
        """
    
        # Add the question to the list of questions.
        api = API_INSTANCES[api_id]
        if self.current_chat is None:

            chat = Chat(identifier=str(uuid7()), title=default_title, history=[])
            self.chats[chat.identifier] = chat
            self.current_chat = chat.identifier
            yield

        else:
            chat = self.chats[self.current_chat]

        qa = QA(identifier=str(uuid7()), question=question, answer="")
        chat.history.append(qa)
    
        # Clear the input and start the processing.
        self.processing = True
        yield

        title = await api.generate_title(question, default=default_title)
        self.chats[chat.identifier].title = title
        yield
    
        # Stream the results, yielding after every word.
        async for answer_text in api.process_chat(chat):
            # Ensure answer_text is not None before concatenation
            if answer_text is not None:
                chat.history[-1].answer += answer_text
            else:
                # Handle the case where answer_text is None, perhaps log it or assign a default value
                # For example, assigning an empty string if answer_text is None
                answer_text = ""
                chat.history[-1].answer += answer_text
            self.chats = self.chats
            yield

        await api.save_chat(chat)
        self.processing = False
        yield

    async def on_key_down(self, key: str):
        if self.previous_key == 'Shift' and key == 'Enter':
            self.multiline = True
        elif key == 'Enter' and not self.multiline:
            yield rx.call_script('document.querySelector("#question-submit").click()')
        self.previous_key = key
        yield