import reflex as rx

from ragnroll_web.state import State

def navbar() -> rx.Component:
    return rx.chakra.box(
        rx.chakra.hstack(
            rx.chakra.spacer(flex=1),
            rx.chakra.icon(
                tag="hamburger",
                on_click=State.toggle_drawer,
                width="1.5em",
                height="1.5em",
                _hover={"cursor": "pointer"},
                display="flex",
                mr=3,
            ),
            
            rx.chakra.spacer(flex=4, display=["none", "none", "none", "flex", "flex"]),
            rx.chakra.spacer(flex=0.5),
            
            rx.chakra.box(
                rx.chakra.center(
                    rx.chakra.input(
                        flex=4,
                        placeholder="Search here...",
                        id="search_input",
                        on_change=State.set_query,
                        on_key_down=State.handle_enter,
                    ),
                    rx.chakra.button(
                        rx.chakra.icon(tag="search2"),
                        width="45%",
                        flex=0.5,
                        on_click=State.handle_submit,
                    ),
                ),
                flex=12,
            ),
            
            rx.chakra.spacer(flex=3),
            
            rx.chakra.hstack(
                rx.chakra.button(
                    rx.chakra.icon(
                        tag="bell"
                    ),
                    variant="ghost"
                ),
                rx.chakra.menu(
                    rx.chakra.menu_button(
                        rx.chakra.avatar(name="John Doe", size="sm")
                    ),
                    rx.chakra.menu_list(
                        rx.chakra.menu_item("My profile"),
                        rx.chakra.menu_divider(),
                        rx.chakra.menu_item("Settings"),
                        rx.chakra.menu_item("Help"),
                    ),
                ),
                
                spacing="2em",
                display=["none", "none", "none", "flex", "flex", "flex", "flex"],
                align_items="center",
            ),
            rx.chakra.spacer(flex=1),
            align_items="center",
        ),
        bg="rgba(255,255,255, 0.9)",
        backdrop_filter="blue(10px)",
        padding_y=["0.8em", "0.8em", "0.5em"],
        border_bottom="1px solid #F4F3F6",
        width="100%",
        position="sticky",
        z_index="999",
        top="0",
        id="navbar"
    )