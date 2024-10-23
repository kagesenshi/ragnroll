"""A custom component for a chat interface."""

from __future__ import annotations

import reflex as rx

from typing import Callable, Generator, Type

import reflex as rx
from .chat import chat, action_bar, history
from .state import State
from .api import API, API_INSTANCES

class Babble(rx.ComponentState):
    """A chat component with state."""

    @classmethod
    def get_component(cls, api: API, **props) -> rx.Component:
        api_id = api.get_identifier()
        API_INSTANCES[api_id] = api
        return rx.hstack(
            rx.vstack(
                rx.button(rx.text('New Chat'), size='2', width="100%"),
                history(width="100%"),
                width="20%",
            ),
            rx.vstack(
                chat(),
                action_bar(api_id),
                background_color=rx.color("mauve", 1),
                color=rx.color("mauve", 12),
                min_height="100vh",
                align_items="stretch",
                spacing="0",
                width="80%"
            ), **props
        )


babble = Babble.create
