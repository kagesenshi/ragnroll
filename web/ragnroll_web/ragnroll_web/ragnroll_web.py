"""Welcome to Reflex! This file outlines the steps to create a basic app."""
from rxconfig import config

from ragnroll_web.components import navbar, sidebar, login, searchResult, featuredSnippet, knowledgepanel
from ragnroll_web.state import State

import reflex as rx

def index() -> rx.Component:

    return rx.vstack(
        navbar(),
        sidebar(),

        # alert box 
        rx.cond(
            State.alert_message,
            rx.alert(
                rx.alert_icon(),
                rx.alert_title(
                    State.alert_message
                ),
                status = "error",
            ),
        ),
        rx.hstack(
            rx.box(width="23%"),
            rx.vstack(
                featuredSnippet(),
                searchResult(),
            ),
            rx.cond(
                State.has_kp,
                knowledgepanel(),
                None,
            ),
            rx.box(width="10%"), #acts a spacer
            justify="end", #moves the components to the right side(end)
            align_items="start", #align to top vertically
            justify_contents="center",
        ),
        justify="start",
    )
    
# Add state and page to the app.
app = rx.App()
app.add_page(index)
# app.compile()
