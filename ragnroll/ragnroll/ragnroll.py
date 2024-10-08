"""Welcome to Reflex! This file outlines the steps to create a basic app."""

from .components.snippet.barchart import barchart_snippet
from .components.snippet.table import table_snippet
from rxconfig import config # type: ignore
import reflex 

config : reflex.Config = config

from .components import (
    navbar,
    text_snippet
)
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

def render_snippet(item: state.SearchResultItem):
    return rx.match(item.visualization,
        ('text-answer', text_snippet(item)),
        ('table', table_snippet(item)),
        ('bar-chart', barchart_snippet(item)),
        rx.text("Unsupported visualization : ", item.visualization)
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
                    rx.cond(
                        state.State.search_results,
                        rx.foreach(state.State.search_results,render_snippet),
                        rx.text("No search results")
                    ),
                    width='100%'
                )
            ),
            width="100%"
        ),
    )




# Add state and page to the app.
app = rx.App()
from .backend.app import app as api_app
# app.compile()
