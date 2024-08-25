import reflex as rx

from ..state import State

def navbar() -> rx.Component:
    return rx.hstack(
            rx.drawer.root(
                rx.drawer.trigger(
                    rx.button(rx.icon(
                        tag="menu",
                        size=32,
                    ), 
                    padding="8px",
                    margin_left="1em",
                    variant='ghost')
                ),
                rx.drawer.overlay(),
                rx.drawer.portal(
                    rx.drawer.content(
                        rx.unordered_list(
                            rx.list_item(
                                rx.link(rx.text('Search'), href='/')
                            ),
                            list_style_type='none'
                        ),
                        top="auto",
                        right="auto",
                        height="100%",
                        width="20em",
                        padding="2em",
                        background_color="#fff",
                    )
                ),
                direction="left",
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
