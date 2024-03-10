import reflex as rx
import time
import asyncio

from ragnroll_web.state import State

def featuredSnippet() -> rx.Component:
    accordion = rx.accordion.root(
        rx.foreach(
            State.snippet_queries,
            lambda item, idx: rx.accordion.item(
                header=rx.text("Query ",idx, as_='span'),
                content=rx.vstack(
                    rx.text('Query'),
                    rx.code_block(
                        item["query"],
                        language="cypher",
                        show_line_numbers=True,
                    ),
                    rx.text('Result'),
                    rx.code_block(
                        item["result"],
                        language="json",
                        show_line_numbers=True,
                    ),
                    font_size="10pt",
                    padding_left="10px",
                    padding_right="10px"
                ),
            ),
        ),
        type="multiple",
        variant="outline",
        width="100%",
    )

    return rx.cond(
        State.snippet,
        rx.vstack(
            rx.card(rx.chakra.text(State.snippet), vertical_align="top", width="100%"),
            accordion,
            id="featuredSnippet",
            width="100%",
            padding_left="100px",
            padding_right="100px",
        ),
    )
