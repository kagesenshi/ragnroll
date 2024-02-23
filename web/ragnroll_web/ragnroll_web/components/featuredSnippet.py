import reflex as rx
import time
import asyncio

from ragnroll_web.state import State

def box_style() -> dict:
    return{
        # "bg": "rgb(250, 250, 250)",
        "bg": "white",
        "border_radius": "15px",
        "border_color": "lightgrey",
        "border_width": "thin",
        "padding": 5,
        "style": {
            "boxShadow": "0px 0px 4px rgba(0, 0, 0, 0.1)",
        },
        "width": "620px",
    }
    
def definition_template() -> rx.Component:
    styles = box_style()
    return rx.box(
        rx.text(State.snippet),
        **styles,
    )
    
def featuredSnippet() -> rx.Component:
    return rx.box(
        rx.cond(
            State.searching, 
            rx.box(rx.spinner()),
            rx.cond(
                State.snippet,
                definition_template(),
                None,
            ),
        ),
        rx.cond(
            State.snippet_queries,
            rx.foreach(
                State.snippet_queries,
                lambda item: rx.box(
                    rx.text(item)
                )
            ),
            None
        )
    )    
