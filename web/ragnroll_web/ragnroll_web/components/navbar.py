import reflex as rx

from ragnroll_web.state import State

def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.drawer.root(
                rx.drawer.trigger(
                    rx.chakra.icon(
                        tag="hamburger",
                        width="1.5em",
                        height="1.5em",
                        _hover={"cursor": "pointer"},
                        display="flex",
                        mr=3,
                    ),
                ),
                rx.drawer.overlay(),
                rx.drawer.portal(
                    rx.drawer.content(
                        rx.unordered_list(
                            rx.list_item(
                                rx.link(rx.text("Train QA"), href='/train')
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
            rx.box(
                rx.center(
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
            rx.hstack(
                rx.chakra.button(rx.chakra.icon(tag="bell"), variant="ghost"),
                rx.chakra.menu(
                    rx.chakra.menu_button(rx.chakra.avatar(name="John Doe", size="sm")),
                    rx.chakra.menu_list(
                        rx.chakra.menu_item("My profile"),
                        rx.chakra.menu_divider(),
                        rx.chakra.menu_item("Settings"),
                        rx.chakra.menu_item("Help"),
                    ),
                ),
                align_items="center",
            ),
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
        id="navbar",
    )
