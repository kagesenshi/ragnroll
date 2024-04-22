"""Welcome to Reflex! This file outlines the steps to create a basic app."""

from rxconfig import config

from ragnroll_web.components import (
    navbar,
    text_snippet,
    table_snippet,
    barchart_snippet
)
from .components.crud import crud_page
from .components.util import wrap_search
import reflex as rx
from . import state


def main_template(component: rx.Component, **kwargs):
    return rx.vstack(
        navbar(),
        # alert box
        rx.cond(
            state.Session.alert_message,
            rx.chakra.alert(
                rx.chakra.alert_icon(),
                rx.chakra.alert_title(state.Session.alert_message),
                status="error",
            ),
        ),
        rx.vstack(component, width="100%", margin_left="20px", margin_right="20px"),
        width="100%",
        **kwargs
    )

@rx.page(route='/')
def index() -> rx.Component:
    return main_template(
        rx.vstack(
            rx.form(
                rx.vstack(
                    rx.flex(
                        rx.spacer(),
                        rx.center(
                            rx.input(placeholder="Search here ...",
                                size="3",
                                width="30em",
                                name="question"
                            ),
                            rx.button(rx.icon(tag="search"), size="3"),
                            spacing="2"
                        ),
                        rx.spacer(),
                        width="100%",
                    )
                ),
                on_submit=state.Session.handle_submit,
                width="100%"
            ),
            wrap_search(
                rx.vstack(
                    text_snippet(),
                    table_snippet(),
                    barchart_snippet(),
                    width='100%'
                )
            ),
            width="100%"
        ),
    )




# Add state and page to the app.
app = rx.App()
# app.compile()
