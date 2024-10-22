from ..templates import template
import reflex as rx
from reflex_babble import babble, api


@template(route="/chat", title="Chat")
def chat_page() -> rx.Component:
    """The table page.

    Returns:
        The UI for the table page.
    """
    return rx.vstack(
        rx.heading("Table", size="5"),
        babble(width="100%"),
        spacing="8",
        width="100%",
    )
