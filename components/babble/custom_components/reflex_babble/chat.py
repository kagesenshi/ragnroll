import reflex as rx
import reflex.vars as rxvars
import reflex_chakra as rxchakra
from .components import loading_icon, resizable_textarea, three_dots_loading_icon
from .state import ChatStateMixin, ChatMessage, Chat, Model
from . import styles
from typing import Callable, Optional
import hashlib

message_style = dict(
    display="inline-block",
    padding="1em",
    border_radius="8px",
    max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
)


def dropdown_menu(*, chat_id: str, chat_title: str, 
                     on_chat_delete: Callable[[str], None]):
    return rx.menu.root(
        rx.menu.trigger(rx.icon("ellipsis-vertical")),
        rx.menu.content(
            rx.dialog.root(
                rx.dialog.trigger(
                    rx.box(
                        "Delete",
                        width="100%",
                        style={
                            "_hover": {
                                "background_color": rx.color("accent", 10),
                                "color": rx.color("accent", 1),
                                "cursor": "pointer",
                            }
                        },
                        class_name="rt-BaseMenuItem rt-DropdownMenuItem",
                    )
                ),
                rx.dialog.content(
                    rx.dialog.title("Delete chat?"),
                    rx.dialog.description(
                        "Are you sure you want to delete this chat titled : "
                        + chat_title
                    ),
                    rx.vstack(
                        rx.divider(),
                        rx.hstack(
                            rx.dialog.close(
                                rx.button(
                                    "Yes",
                                    size="3",
                                    variant="outline",
                                    on_click=lambda: on_chat_delete(
                                        chat_id
                                    ).debounce(500),
                                )
                            ),
                            rx.dialog.close(rx.button("No", size="3")),
                        ),
                    ),
                ),
            ),
        ),
    )


def menu_item(*, current_chat: str, chat_id: str, chat_title: str, 
              on_chat_change: Callable[[str], None],
              on_chat_delete: Callable[[str], None]) -> rx.Component:
    """Menu item.

    Args:
        text: The text of the item.
        url: The URL of the item.

    Returns:
        rx.Component: The menu item component.
    """
    # Whether the item is active.
    active = current_chat == chat_id
    return rx.hstack(
        rx.text(
            chat_title, weight="regular",
            width="100%",
            on_click=lambda: on_chat_change(chat_id),
        ),
        rx.spacer(),
        dropdown_menu(chat_title=chat_title, chat_id=chat_id, 
                      on_chat_delete=on_chat_delete),
        style={
            "_hover": {
                "background_color": rx.cond(
                    active,
                    styles.accent_bg_color,
                    styles.gray_bg_color,
                ),
                "color": rx.cond(
                    active,
                    styles.accent_text_color,
                    styles.text_color,
                ),
                "cursor": "pointer"
            },
            "opacity": rx.cond(
                active,
                "1",
                "0.80",
            ),
            "font-weight": rx.cond(
                active,
                "bold",
                "normal"
            )
        },
        align="center",
        width="100%",
        border_radius=styles.border_radius,
        padding="0.35em",
        opacity=rx.cond(
            active,
            "1",
            "0.8",
        ),
    )


def message(message: ChatMessage) -> rx.Component:
    """A single question/answer message.

    Args:
        qa: The question/answer pair.

    Returns:
        A component displaying the question/answer pair.
    """
    return rx.box(
        rx.cond(
            message.role == "user",
            rx.box(
                rx.html(
                    message.message,
                    background_color=rx.color("mauve", 4),
                    color=rx.color("mauve", 12),
                    **message_style,
                ),
                text_align="right",
                margin_top="1em",
            ),
        ),
        rx.cond(
            message.role == "assistant",
            rx.box(
                rx.html(
                    message.message,
                    background_color=rx.color("accent", 4),
                    color=rx.color("accent", 12),
                    **message_style,
                ),
                text_align="left",
                padding_top="1em",
            ),
        ),
        width="100%",
    )


def chat(*, current_chat:str, current_chat_rendered: list[ChatMessage], processing_state: bool, ) -> rx.Component:
    """List all the messages in a single conversation."""
    return rx.vstack(
        rx.cond(
            current_chat == None,
            rx.box(
                rx.heading("What can I help with?", align="center"),
                width="100%",
                margin_top="200px",
            ),
            rx.box(
                rx.foreach(current_chat_rendered, message),
                rx.cond(
                    processing_state,
                    rx.box(
                        three_dots_loading_icon(height="0.5em"),
                        text_align="left",
                        padding_top="1em",
                    ),
                ),
                width="100%",
                class_name="conversation",
            ),
        ),
        class_name="chatbox",
        py="8",
        flex="1",
        width="100%",
        max_width="50em",
        padding_x="4px",
        align_self="center",
        overflow="hidden",
        padding_bottom="5em",
    )


def action_bar(
    *,
    models: list[Model],
    processing_state: bool,
    current_model: str,
    on_model_select: Callable[[str], None],
    on_message_submit: Callable[[dict[str, str]], None],
    disclaimer: Optional[str] = None
) -> rx.Component:

    return rx.center(
        rx.vstack(
            rxchakra.form(
                rxchakra.form_control(
                    rx.hstack(
                        rx.select.root(
                            rx.select.trigger(),
                            rx.select.content(
                                rx.select.group(
                                    rx.select.label("Model"),
                                    rx.foreach(models, lambda m:
                                        rx.select.item(m.title, value=m.name)
                                    )
                                )
                            ),
                            default_value=current_model,
                            on_change=on_model_select,
                            name="model",
                        ),
                        resizable_textarea(
                            placeholder="Type something...",
                            id="question",
                            width=["10em", "15em", "20em", "30em", "45em", "50em"],
                            auto_height=True,
                            padding="5pt",
                        ),
                        rx.button(
                            rx.cond(
                                processing_state,
                                loading_icon(height="1em"),
                                rx.text("Send"),
                            ),
                            id="question-submit",
                            type="submit",
                        ),
                        align_items="center",
                    ),
                    is_disabled=processing_state,
                ),
                on_submit=lambda form_data: on_message_submit(form_data),
                reset_on_submit=True,
            ),
            rx.text(
                rx.cond(
                    disclaimer,
                    disclaimer,
                    "ReflexGPT may return factually incorrect or misleading responses. Use discretion."
                ),
                text_align="center",
                font_size=".75em",
                color=rx.color("mauve", 10),
            ),
            align_items="center",
        ),
        position="sticky",
        bottom="0",
        left="0",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        align_items="stretch",
        width="100%",
    )


def history(*, chats: list[Chat],  
            current_chat: str, 
            on_chat_change: Callable[[str], None],
            on_chat_delete: Callable[[str], None],
            **props) -> rx.Component:
    return rx.vstack(
        rx.foreach(
            chats,
            lambda entry: menu_item(
                current_chat=current_chat,
                chat_id=entry.identifier,
                chat_title=entry.title,
                on_chat_change=on_chat_change,
                on_chat_delete=on_chat_delete,
            ),
        ),
        spacing="0",
        **props,
    )
