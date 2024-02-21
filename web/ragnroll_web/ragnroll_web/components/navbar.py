import reflex as rx

from ragnroll_web.state import State

def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.spacer(flex=1),
            rx.icon(
                tag="hamburger",
                on_click=State.toggle_drawer,
                width="1.5em",
                height="1.5em",
                _hover={"cursor": "pointer"},
                display="flex",
                mr=3,
            ),
            
            rx.spacer(flex=4, display=["none", "none", "none", "flex", "flex"]),
            rx.spacer(flex=0.5),
            
            rx.box(
                rx.center(
                    rx.input(
                        flex=4,
                        placeholder="Search here...",
                        id="search_input",
                        on_change=State.set_query,
                        on_key_down=State.handle_enter,
                    ),
                    rx.button(
                        rx.icon(tag="search2"),
                        width="45%",
                        flex=0.5,
                        on_click=State.handle_submit,
                    ),
                ),
                flex=12,
            ),
            
            rx.spacer(flex=3),
            
            rx.hstack(
                rx.button(
                    rx.icon(
                        tag="bell"
                    ),
                    variant="ghost"
                ),
                rx.menu(
                    rx.menu_button(
                        rx.avatar(name="John Doe", size="sm")
                    ),
                    rx.menu_list(
                        rx.menu_item("My profile"),
                        rx.menu_divider(),
                        rx.menu_item("Settings"),
                        rx.menu_item("Help"),
                    ),
                ),
                
                spacing="2em",
                display=["none", "none", "none", "flex", "flex", "flex", "flex"],
                align_items="center",
            ),
            rx.spacer(flex=1),
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
    )