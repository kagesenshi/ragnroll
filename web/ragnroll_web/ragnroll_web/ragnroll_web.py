"""Welcome to Reflex! This file outlines the steps to create a basic app."""

from rxconfig import config

from ragnroll_web.components import (
    navbar,
    sidebar,
    login,
    searchResult,
    featuredSnippet,
    knowledgepanel,
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
                featuredSnippet(),
            ),
            width="100%"
        ),
    )

@rx.page(route='/retrieval_query')
def retrieval_query() -> rx.Component:

    return main_template(
        crud_page(
            "Retrieval Queries",
            state.QueryCRUD,
            create_form=rx.form(
                rx.flex(
                    rx.text("Query"),
                    rx.input(name='query'),
                    rx.flex(
                        rx.dialog.close(
                            rx.button("Cancel", color_scheme="red", variant="soft"),
                            on_click=state.QueryCRUD.refresh,
                        ),
                        rx.dialog.close(
                            rx.button("Save", type='submit')
                        ),
                        direction="row-reverse",
                        spacing="3",
                    ),
                    direction="column",
                    spacing="3",
                ),
                on_submit=state.QueryCRUD.create,
                reset_on_submit=True
            ),
            actions=lambda row, rowidx: rx.hstack(
                rx.link(
                    rx.button("Manage Questions"), href=f'/retrieval_query/{row["id"]}'
                ),
                rx.dialog.root(
                    rx.dialog.trigger(rx.button(rx.icon(tag="trash"))),
                    rx.dialog.content(
                        rx.dialog.title("Delete"),
                        rx.dialog.description("Are you sure?"),
                        rx.hstack(
                            rx.dialog.close(
                                rx.button(
                                    "Delete",
                                    color_scheme="red",
                                    on_click=state.QueryCRUD.delete(row["id"]),
                                )
                            ),
                            rx.dialog.close(rx.button("Cancel")),
                        ),
                    ),
                ),
            ),
            on_mount=state.QueryCRUD.refresh,
        )
    )


@rx.page(route="/retrieval_query/[node_id]")
def retrieval_query_view() -> rx.Component:
    return main_template(
        crud_page(
            "Retrieval Question",
            state.QuestionCRUD,
            create_form=rx.form(
                rx.flex(
                    rx.text("Question"),
                    rx.input(name="question"),
                    rx.flex(
                        rx.dialog.close(
                            rx.button("Cancel", color_scheme="red", variant="soft"),
                            on_click=state.QuestionCRUD.refresh,
                        ),
                        rx.dialog.close(rx.button("Save", type="submit")),
                        direction="row-reverse",
                        spacing="3",
                    ),
                    direction="column",
                    spacing="3",
                ),
                on_submit=state.QuestionCRUD.create,
                reset_on_submit=True,
            ),
            actions=lambda row, rowidx: rx.hstack(
                rx.dialog.root(
                    rx.dialog.trigger(rx.button(rx.icon(tag="trash"))),
                    rx.dialog.content(
                        rx.dialog.title("Delete"),
                        rx.dialog.description("Are you sure?"),
                        rx.hstack(
                            rx.dialog.close(
                                rx.button(
                                    "Delete",
                                    color_scheme="red",
                                    on_click=state.QuestionCRUD.delete(row["id"]),
                                )
                            ),
                            rx.dialog.close(rx.button("Cancel")),
                        ),
                    ),
                ),
            ),

            on_mount=state.QuestionCRUD.refresh,
        )
    )


# Add state and page to the app.
app = rx.App()
# app.compile()
