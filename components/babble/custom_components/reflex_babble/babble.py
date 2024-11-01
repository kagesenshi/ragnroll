"""A custom component for a chat interface."""

from __future__ import annotations

import reflex as rx

from typing import Callable, Generator, Type

import reflex as rx
from .chat import chat, action_bar, history
from .state import ChatStateMixin

class Babble(rx.ComponentState):
    """A chat component with state."""

    @classmethod
    def get_component(cls, state_cls: type['ChatStateMixin'], **props) -> rx.Component:
        return rx.hstack(
            rx.vstack(
                rx.button(rx.text('New Chat'), size='2', width="100%", on_click=state_cls.new_chat_handler),
                rx.cond(state_cls.chats, rx.text.strong("Recent chats")),
                history(state_cls, width="100%"),
                width="20%",
            ),
            rx.vstack(
                chat(state_cls),
                action_bar(state_cls),
                background_color=rx.color("mauve", 1),
                color=rx.color("mauve", 12),
                min_height="100vh",
                align_items="stretch",
                spacing="0",
                width="80%"
            ), **props
        )


babble = Babble.create
