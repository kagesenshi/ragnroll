import reflex as rx

from ragnroll_web.state import State

def sidebar() -> rx.Component:
    return rx.chakra.drawer(
        rx.chakra.drawer_overlay(),
        rx.chakra.drawer_content(
            rx.chakra.drawer_header("Logo"),
            rx.chakra.drawer_body(
                rx.chakra.menu(
                    rx.chakra.link(
                        rx.chakra.menu_item(
                            rx.chakra.icon(mr=3, tag="search"),
                            "Browse"
                        ),
                        # href="/"
                    ),
                    rx.chakra.link(
                        rx.chakra.menu_item(
                            rx.chakra.icon(mr=3, tag="question"),
                            "Login",
                        ),
                        href="/login"
                    ),
                ),
            ),
            rx.chakra.drawer_footer(
                rx.chakra.button(
                    "Close",
                    on_click=State.toggle_drawer,
                )
            ),
            bg="rgba(255, 255, 255, 1.0)",
        ),
        is_open=State.drawer_open,
        placement="left",
        on_overlay_click=State.toggle_drawer,
        on_esc=State.toggle_drawer,
        id="drawer"
    )