"""Welcome to Reflex! This file outlines the steps to create a basic app."""
from rxconfig import config

from ragnroll_web.components import navbar, sidebar, login, searchResult, featuredSnippet, knowledgepanel
from ragnroll_web.state import State
from .components.util import wrap_search
import reflex as rx


def index() -> rx.Component:

    return rx.chakra.vstack(
        navbar(),
        sidebar(),
        # alert box
        rx.cond(
            State.alert_message,
            rx.chakra.alert(
                rx.chakra.alert_icon(),
                rx.chakra.alert_title(State.alert_message),
                status="error",
            ),
        ),
        wrap_search(
            featuredSnippet(),
        ),
        width="100%",
    )


# Add state and page to the app.
app = rx.App()
app.add_page(index)
# app.compile()
