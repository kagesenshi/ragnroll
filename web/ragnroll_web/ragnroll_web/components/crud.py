import reflex as rx
import typing
from .. import state


def crud_page(name: str, state: state.CRUD, create_form: rx.Component) -> rx.Component:
    # this should return a table with an add button
    return rx.vstack(
        rx.hstack(
            rx.dialog.root(
                rx.dialog.trigger(rx.button("Add %s" % name)),
                rx.dialog.content(
                    rx.dialog.title("Add %s" % name),
                    rx.dialog.description("Create new %s" % name),
                    create_form,
                ),
                on_open_change=state.dialog_on_open_change,
            )
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.foreach(
                        state.columns,
                        lambda col, colidx: rx.table.column_header_cell(col["title"]),
                    )
                )
            ),
            rx.cond(
                state.reloading,
                rx.chakra.spinner(size="md"),
                rx.table.body(
                    rx.foreach(
                        state.data,
                        lambda row, rowidx: rx.table.row(
                            rx.foreach(
                                state.columns,
                                lambda col, colidx: rx.table.cell(row[col["name"]]),
                            )
                        ),
                    )
                ),
            ),
            spacing="2",
            width="100%",
        ),
        rx.flex(
            rx.cond(state.prev_url, rx.button("<", on_click=state.enter_prev_page)),
            rx.button(rx.text(state.current_page), color_scheme="gray", variant="soft"),
            rx.cond(state.next_url, rx.button(">", on_click=state.enter_next_page)),
            align="end",
        ),
        width="100%",
    )
