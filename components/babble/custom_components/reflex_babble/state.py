import os
import reflex as rx
from openai import OpenAI
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from typing import Callable, AsyncGenerator, Any, TypedDict, Optional, Literal
from .settings import settings 
import abc 
from uuid_extensions import uuid7
from datetime import datetime
import pytz

class ChatMessage(rx.Base):

    identifier: str
    timestamp: datetime
    role: Literal['assistant', 'user']
    message: str

class Chat(rx.Base):

    identifier: str
    timestamp: datetime
    title: str
    history: list[ChatMessage]    


def render_markdown(text: str) -> str:
    return markdown.markdown(text, extensions=[CodeHiliteExtension(linenums=False), FencedCodeExtension()])

class ChatStateMixin(rx.State, mixin=True):
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

    api_id: str

    @classmethod
    def get_parent_state(cls):
        # FIXME: Workaround 
        return rx.State

    @abc.abstractmethod
    def get_identifier(self) -> str:
        raise NotImplemented

    async def httpx_connection_options(self) -> dict[str, Any]:
        return {}

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

    @abc.abstractmethod
    async def load_chats(self) -> list[Chat]:
        pass

    async def new_chat_handler(self):
        self.current_chat = None

    async def delete_chat_handler(self, chat_id: str):
        """Delete the current chat."""
        if self.current_chat == chat_id:
            self.current_chat = None
            yield
        await self.delete_chat(chat_id)
        self.chats = {}

    async def set_chat_handler(self, chat_id: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        await self.set_chat(chat_id)
        self.current_chat = chat_id

    async def load_chats_handler(self):
        if self.chats:
            return 

        chats = await self.load_chats()
        if len(chats) == 0:
            self.current_chat = None
            yield
        self.chats = dict([(c.identifier, c) for c in chats])

    @rx.var
    def sorted_chats(self) -> list[Chat]:
        return list(sorted(self.chats.values(), key=lambda x: x.timestamp, reverse=True))

    @rx.var
    def rendered_current_chat(self) -> list[ChatMessage]:
        res = []
        if self.current_chat is None:
            return []
        for c in self.chats[self.current_chat].history:
            res.append(
                ChatMessage(
                    identifier=c.identifier,
                    timestamp=c.timestamp,
                    role=c.role,
                    message=render_markdown(c.message),
                )
            )
        return res

    async def process_question_handler(self, form_data: dict[str, str]):
        # Get the question from the form

        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return

        if not question:
            return

        if self.multiline:
            self.multiline = False

        async for value in self._process_question_handler(question):
            yield value

    async def _process_question_handler(self, question: str, default_title: str = 'New chat'):
        """Get the response from the API.
    
        Args:
            form_data: A dict with the current question.
        """

        # Add the question to the list of questions.
        new_chat = False
        if self.current_chat is None:

            chat = Chat(identifier=str(uuid7()), title=default_title, history=[], timestamp=datetime.now(pytz.UTC))
            self.chats[chat.identifier] = chat
            self.current_chat = chat.identifier
            new_chat = True
            yield

        else:
            chat = self.chats[self.current_chat]

        user_msg = ChatMessage(
            identifier=str(uuid7()),
            timestamp=datetime.now(pytz.UTC),
            role='user',
            message=question
        )
        chat.history.append(user_msg)
        # Clear the input and start the processing.
        self.processing = True
        yield

        if new_chat:
            title = await self.generate_title(question, default=default_title)
            self.chats[chat.identifier].title = title
            yield

        assistant_msg = ChatMessage(
            identifier=str(uuid7()),
            timestamp=datetime.now(pytz.UTC),
            role='assistant',
            message=""
        )
        chat.history.append(assistant_msg)

        # Stream the results, yielding after every word.
        async for answer_text in self.process_chat(chat):
            # Ensure answer_text is not None before concatenation
            if answer_text is not None:
                assistant_msg.message += answer_text
            else:
                # Handle the case where answer_text is None, perhaps log it or assign a default value
                # For example, assigning an empty string if answer_text is None
                answer_text = ""
                assistant_msg.message += answer_text
            self.chats = self.chats
            yield


        await self.save_chat(chat)
        self.processing = False
        yield


    async def on_key_down(self, key: str):
        if self.previous_key == 'Shift' and key == 'Enter':
            self.multiline = True
        elif key == 'Enter' and not self.multiline:
            yield rx.call_script('document.querySelector("#question-submit").click()')
        self.previous_key = key
        yield
