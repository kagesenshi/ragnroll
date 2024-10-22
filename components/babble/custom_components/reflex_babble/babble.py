"""A custom component for a chat interface."""

from __future__ import annotations

import reflex as rx

from typing import Callable, Generator, Type

import reflex as rx
from .api import default_process
from .chat import chat, action_bar

class Babble(rx.ComponentState):
    """A chat component with state."""

    @classmethod
    def get_component(cls, **props) -> rx.Component:
        return rx.vstack(
            chat(),
            action_bar(),
            background_color=rx.color("mauve", 1),
            color=rx.color("mauve", 12),
            min_height="100vh",
            align_items="stretch",
            spacing="0",
            **props
        )


babble = Babble.create
