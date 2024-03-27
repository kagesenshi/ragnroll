import reflex as rx
from ..state import State

def wrap_search(component: rx.Component) -> rx.Component:
    return rx.cond(
        State.searching,
        rx.flex(
            rx.center(
                rx.chakra.spinner(size='xl'),
                width='100%'
            ),
            width="100%",
            height="200px"
        ),
        component,
    )