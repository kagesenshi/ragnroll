import reflex as rx

from ragnroll_web.state import State

def sidebar() -> rx.Component:
    return rx.drawer(
        rx.drawer_overlay(),
        rx.drawer_content(
            rx.drawer_header("Logo"),
            rx.drawer_body(
                rx.menu(
                    rx.link(
                        rx.menu_item(
                            rx.icon(mr=3, tag="search"),
                            "Browse"
                        ),
                        # href="/"
                    ),
                    rx.link(
                        rx.menu_item(
                            rx.icon(mr=3, tag="question"),
                            "Login",
                        ),
                        href="/login"
                    ),
                ),
            ),
            rx.drawer_footer(
                rx.button(
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
    )