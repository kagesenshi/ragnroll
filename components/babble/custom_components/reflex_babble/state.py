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
import traceback
import pytz
import time
import asyncio

SCROLL_BOTTOM = rx.call_script("""
    window.scrollTo({
        top: (window.innerHeight > (document.getElementsByClassName('conversation')[0].scrollHeight + 300)) ? 0 : document.body.scrollHeight ,
        behavior: 'smooth'});
    """)

class ChatMessage(rx.Base):

    identifier: str
    timestamp: datetime
    role: Literal['assistant', 'user']
    message: str
    model: Optional[str] = None

class Chat(rx.Base):

    identifier: str
    timestamp: datetime
    title: str
    history: list[ChatMessage]    

class Model(rx.Base):

    name: str
    title: str

def render_markdown(text: str) -> str:
    return markdown.markdown(text, extensions=[CodeHiliteExtension(linenums=False), FencedCodeExtension()])

class ChatStateMixin(rx.State, mixin=True):
    """The app state."""

    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, Chat] = {}

    # The current chat name.
    current_chat: Optional[str] = None

    # current selected model
    current_model: Optional[str] = None

    # available models
    available_models: list[Model] = []

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    input_value: str = ''

    previous_key: str = ''

    multiline: bool = False

    api_id: str

    default_title: str = 'New Chat'

    last_refresh: float = 0

    @rx.var
    def sorted_chats(self) -> list[Chat]:
        return list(sorted(self.chats.values(), key=lambda x: x.timestamp, reverse=True))

    @rx.var
    def rendered_current_chat(self) -> list[ChatMessage]:
        res = []
        if self.current_chat is None:
            return []
        if self.current_chat not in self.chats:
            self.current_chat = None
            return []
        for c in self.chats[self.current_chat].history:
            if c.message:
                res.append(
                    ChatMessage(
                        identifier=c.identifier,
                        timestamp=c.timestamp,
                        role=c.role,
                        message=render_markdown(c.message),
                        model=c.model,
                    )
                )
        return res
    
    async def on_mount(self):
        now = time.time()
        if self.chats and (now - self.last_refresh < 300):
            return 

        chats = await self.load_chats()
        if len(chats) == 0:
            self.current_chat = None
            yield

        self.chats = dict([(c.identifier, c) for c in chats])

        models = await self.load_models()
        self.available_models = models
        if not self.current_model and models:
            self.current_model = models[0].name
    
        if len(chats) == 0 and len(models) == 0:
            yield self.__class__.on_mount_refresh

    @rx.background
    async def on_mount_refresh(self):
        await asyncio.sleep(1)
        async with self:
            res = []
            async for i in self.on_mount():
                res.append(i)
                yield

        for r in res:
            yield r

    async def on_chat_new(self):
        self.current_chat = None

    async def on_chat_change(self, chat_id: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        await self.set_chat(chat_id)
        self.current_chat = chat_id
        yield SCROLL_BOTTOM

    async def on_chat_delete(self, chat_id: str):
        """Delete the current chat."""
        if self.current_chat == chat_id:
            self.current_chat = None
            yield
        try:
            await self.delete_chat(chat_id)
        except AssertionError as e:
            traceback.print_exc()
            yield rx.toast.error("Unable to delete chat")
            return 
        del self.chats[chat_id]
        self.last_refresh = 0
        yield self.__class__.on_mount

    async def on_model_select(self, model_name: str):
        self.current_model = model_name

    async def on_message_submit(self, form_data: dict[str, str]):
        # Get the question from the form
        question = form_data["question"]
        model = form_data["model"]

        if not model:
            yield rx.toast.error("Please select a model")
            return

        # Check if the question is empty
        if question == "":
            return

        if not question:
            return

        if self.multiline:
            self.multiline = False

        # Add the question to the list of questions.
        new_chat = False
        if self.current_chat is None:

            chat = Chat(identifier=str(uuid7()), title=self.default_title, history=[], timestamp=datetime.now(pytz.UTC))
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
            message=question,
            model=None,
        )
        chat.history.append(user_msg)
        # Clear the input and start the processing.
        self.processing = True
        yield

        if new_chat:
            title = await self.generate_title(question, model=model, default=self.default_title)
            self.chats[self.current_chat].title = title
            self.chats = self.chats
            yield

        assistant_msg = ChatMessage(
                identifier=str(uuid7()),
                timestamp=datetime.now(pytz.UTC),
                role='assistant',
                message="",
                model=model
            )
        self.chats[self.current_chat].history.append(assistant_msg)
        msg_idx = self.chats[self.current_chat].history.index(assistant_msg)

        yield self.__class__.bg_process_chat(msg_idx, model)
    
    @rx.background
    async def bg_process_chat(self, msg_idx: int, model: str):
        # Stream the results, yielding after every word.
        async def generator():
            buffer: list[str] = []
            async for answer_text in self.process_chat(self.chats[self.current_chat], model=model):
                if answer_text is not None:
                    buffer.append(answer_text)
                else:
                    buffer.append("")
                if len(buffer) >= 10:
                    yield buffer
                    buffer = []
            yield buffer

        async for chunk in generator():
            # Ensure answer_text is not None before concatenation
            async with self:
                for word in chunk:
                    self.chats[self.current_chat].history[msg_idx].message += word
                    yield
                self.chats = self.chats
                yield SCROLL_BOTTOM

        async with self:
            await self.save_chat(self.chats[self.current_chat])
            self.processing = False

    @classmethod
    def get_parent_state(cls):
        # FIXME: workaround 
        parent_states = [
            base
            for base in cls.__bases__
            if issubclass(base, rx.state.BaseState) and base is not rx.state.BaseState
        ]
        if parent_states and parent_states[0]._mixin == True:
            return rx.State
        return super().get_parent_state()

    @abc.abstractmethod
    async def generate_title(self, question: str, model: str, default: str = 'New chat') -> str:
        raise NotImplemented

    @abc.abstractmethod
    async def process_chat(self, chat: 'Chat', model: str) -> AsyncGenerator[str, None]:
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

    @abc.abstractmethod
    async def load_models(self) -> list[Model]:
        pass