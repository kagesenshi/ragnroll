"""Welcome to Reflex! This file outlines the steps to create a basic app."""
from rxconfig import config

from ragnroll_web.components import navbar, sidebar, login, searchResult, featuredSnippet, knowledgepanel
from .components.crud import crud_page
from .components.util import wrap_search
import reflex as rx
from . import state

def main_template(component: rx.Component, **kwargs):
    return rx.vstack(
        navbar(),
        sidebar(),
        # alert box
        rx.cond(
            state.Session.alert_message,
            rx.chakra.alert(
                rx.chakra.alert_icon(),
                rx.chakra.alert_title(state.Session.alert_message),
                status="error",
            ),
        ),
        rx.vstack(
            component,
            width="100%",
            margin_left="20px",
            margin_right="20px"
        ),
        width="100%",
        **kwargs
    )


def index() -> rx.Component:
    return main_template(
        wrap_search(
            featuredSnippet(),
        )
    )


def train() -> rx.Component:

    return main_template(
        crud_page(
            "Retrieval Question",
            state.QuestionCRUD,
            create_form=rx.flex(
                rx.text("Question"),
                rx.debounce_input(
                    rx.input(on_change=state.QuestionCreateForm.set_question),
                    debounce_timeout=1000
                ),
                rx.flex(
                    rx.dialog.close(rx.button("Cancel", color_scheme='red', variant='soft'), on_click=state.QuestionCRUD.refresh),
                    rx.dialog.close(rx.button('Save'), on_click=state.QuestionCreateForm.submit),
                    direction='row-reverse',
                    spacing='3'
                ),
                direction="column",
                spacing='3'
            ),
        ),
        on_mount=state.QuestionCRUD.refresh,
    )

# Add state and page to the app.
app = rx.App()
app.add_page(index)
app.add_page(train, route='/train')
# app.compile()
