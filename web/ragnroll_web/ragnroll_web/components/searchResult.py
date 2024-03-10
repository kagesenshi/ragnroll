import reflex as rx

from ragnroll_web.state import State
from typing import Dict
from .util import spinner

def box_style() -> dict:
    return{
        "bg": "white",
        "border_radius": "15px",
        "border_color": "whitesmoke",
        "border_width": "thin",
        "padding": 5,
        "width": "620px"
    }
    
def searchResult() -> rx.Component:

    return rx.cond(
            State.search_result_list,
            rx.chakra.vstack(
                rx.foreach(State.search_result_list, searchResultTemplate)
            )
    )
    
def searchResultTemplate(item: Dict[str, str]) -> rx.Component:
    styles = box_style()
    return rx.chakra.box(
        rx.chakra.link(
            item["title"],
            href=item['url'],
            color="rgb(107,99,246)",
            style={"font_size": "1.1rem"},
        ),
        rx.chakra.text(item["description"]),
        **styles,
    )
    
    
    