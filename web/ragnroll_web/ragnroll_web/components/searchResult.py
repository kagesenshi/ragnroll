import reflex as rx

from ragnroll_web.state import State
from typing import Dict

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

    return rx.cond(State.searching, 
         rx.box(rx.spinner(
             
                    color="lightgreen",
                    thickness=5,
                    speed="0.5s",
                    size="xl",
         )),              
         rx.cond(
            State.search_result_list,
            rx.vstack(
                rx.foreach(State.search_result_list, searchResultTemplate)
            ),
            noResultFoundTemplate()
    ))
    
def noResultFoundTemplate() -> rx.Component:
    return rx.box()
#    styles = box_style()
#    return rx.box(
#        rx.text("No results found"),
#        **styles,
#    )
    
def searchResultTemplate(item: Dict[str, str]) -> rx.Component:
    styles = box_style()
    return rx.box(
        # rx.heading(item["cafeName"], size="sm", color="blue"),
        rx.link(
            item["title"],
            href=item['url'],
            color="rgb(107,99,246)",
            style={"font_size": "1.1rem"},
        ),
        rx.text(item["description"]),
        **styles,
    )
    
    
    