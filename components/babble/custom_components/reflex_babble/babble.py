"""A custom component for a chat interface."""

from __future__ import annotations

import reflex as rx

from typing import Callable, Generator, Type

import reflex as rx
from .chat import chat, action_bar, history
from .state import ChatStateMixin, Chat, ChatMessage

class Babble(rx.ComponentState):
    """A chat component with state."""

    @classmethod
    def get_component(cls,
                      *,
                      chats: list[Chat],
                      current_chat: str,
                      current_chat_rendered: list[ChatMessage], 
                      processing_state: bool,
                      on_chat_new: Callable,
                      on_chat_delete: Callable[[str], None],
                      on_chat_change: Callable[[str], None],
                      on_message_submit: Callable[[dict[str, str]], None],
                      on_mount: Callable[[], None],
                      **props) -> rx.Component:
        return rx.hstack(
            rx.vstack(
                rx.button(rx.text('New Chat'), size='2', width="100%", on_click=on_chat_new),
                rx.cond(chats, rx.text.strong("Recent chats")),
                history(chats=chats,
                        current_chat=current_chat,
                        on_chat_change=on_chat_change,
                        on_chat_delete=on_chat_delete,
                        width="100%"),
                width="20%",
            ),
            rx.vstack(
                chat(current_chat_rendered=current_chat_rendered,
                     current_chat=current_chat,
                     processing_state=processing_state),
                action_bar(processing_state=processing_state,
                           on_message_submit=on_message_submit),
                background_color=rx.color("mauve", 1),
                color=rx.color("mauve", 12),
                min_height="100vh",
                align_items="stretch",
                spacing="0",
                width="80%"
            ), 
            on_mount=on_mount,
            **props
        )

    @classmethod
    def create(
        cls,
        *children,
        state_cls: ChatStateMixin,
        **props,
    ) -> rx.Component:
        return super().create(*children, 
                              chats=state_cls.sorted_chats,
               current_chat=state_cls.current_chat,
               current_chat_rendered=state_cls.rendered_current_chat,
               processing_state=state_cls.processing,
               on_chat_new=state_cls.on_chat_new,
               on_chat_delete=state_cls.on_chat_delete,
               on_chat_change=state_cls.on_chat_change,
               on_message_submit=state_cls.on_message_submit,
               on_mount=state_cls.on_mount.debounce(100),
                **props)


babble = Babble.create
