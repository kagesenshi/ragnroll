import reflex as rx

from ..state import State

def navbar_button(text, href):
    return rx.link(
        rx.button(
            rx.text(text), padding="13px", variant='ghost'
        ), 
        href=href
    )


def navbar() -> rx.Component:
    return rx.hstack(
            rx.hstack(
                navbar_button('Search', '/'),
                navbar_button('Expertise', '/expertise'),
                spacing='5',
            ),
            rx.spacer(),
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.icon(tag="bell", size=32), 
                        variant="ghost",
                        padding="8px",
                        margin_left="1em",
                        margin_right="1em"
                    ),                   
                ),
                rx.menu.content(
                    rx.menu.item("notification")
                )
            ),
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.avatar(fallback="JD"),
                        variant='ghost',
                        margin_right="1em"
                    )
                ),
                rx.menu.content(
                    rx.menu.item("My Profile"),
                    rx.menu.separator(),
                    rx.menu.item("Settings"),
                    rx.menu.item("Help")
                )
            ),
            border_bottom="1px solid #F4F3F6",
            position="sticky",
            z_index="2",
            top="0",
            width="100%",
            padding_y=["0.8em", "0.8em", "0.5em"],
            id="navbar",
    )
