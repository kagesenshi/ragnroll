import reflex as rx
from ..state import State

def spinner():
    return rx.chakra.spinner(size='md')

def wrap_search(component: rx.Component) -> rx.Component:
    return rx.cond(
        State.searching,
        spinner(),
        component,
    )