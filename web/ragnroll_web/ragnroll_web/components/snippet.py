import reflex as rx
import time
import asyncio

from ragnroll_web.state import State

def text_snippet() -> rx.Component:
    queries = rx.foreach(
            State.snippet_queries,
            lambda item, idx: rx.vstack(
                    rx.text('Query'),
                    rx.code_block(
                        item["query"],
                        language="cypher",
                        show_line_numbers=True,
                    ),
                    rx.text('Result'),
                    rx.code_block(
                        item["result"],
                        language="json",
                        show_line_numbers=True,
                    ),
                    font_size="10pt",
                    padding_left="10px",
                    padding_right="10px"
                ),
            )

    drawer = rx.drawer.root(
        rx.drawer.trigger(
            rx.button(rx.icon(tag='message_circle_question'))
        ),
        rx.drawer.overlay(z_index='5'),
        rx.drawer.portal(
            rx.drawer.content(
                rx.scroll_area(
                    queries,
                    width="50em",
                    scrollbars='horizontal'
                ),
                width="50em",
                height="100%",
                left="auto",
                top="auto",
                background_color="#FFF"
            ),
        ),
        direction='right'
    )

    return rx.cond(
        State.snippet,
        rx.vstack(
            rx.card(rx.hstack(rx.text(State.snippet), rx.spacer(), drawer), vertical_align="top", width="100%"),
            id="featuredSnippet",
            width="100%",
            padding_left="100px",
            padding_right="100px",
        ),
    )


def table_snippet() -> rx.Component:
    queries = rx.foreach(
            State.table_queries,
            lambda item, idx: rx.vstack(
                    rx.text('Query'),
                    rx.code_block(
                        item["query"],
                        language="cypher",
                        show_line_numbers=True,
                    ),
                    rx.text('Result'),
                    rx.code_block(
                        item["result"],
                        language="json",
                        show_line_numbers=True,
                    ),
                    font_size="10pt",
                    padding_left="10px",
                    padding_right="10px"
                ),
            )

    drawer = rx.drawer.root(
        rx.drawer.trigger(
            rx.button(rx.icon(tag='message_circle_question'))
        ),
        rx.drawer.overlay(z_index='5'),
        rx.drawer.portal(
            rx.drawer.content(
                rx.scroll_area(
                    queries,
                    width="50em",
                    scrollbars='horizontal'
                ),
                width="50em",
                height="100%",
                left="auto",
                top="auto",
                background_color="#FFF"
            ),
        ),
        direction='right'
    )

    return rx.cond(
        State.table_data,
        rx.vstack(
            rx.card(
                rx.vstack(
                    rx.hstack(rx.spacer(), drawer),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.foreach(
                                    State.table_headers,
                                    lambda item, idx: rx.table.column_header_cell(item),
                                )
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                State.table_data, lambda row, idx: rx.table.row(
                                    rx.foreach(
                                        State.table_headers,
                                        lambda item, idx: rx.table.cell(row[item])
                                    )
                                )
                            )
                        ),
                        width="100%"
                    ),
                ),
                vertical_align="top",
                width="100%",
            ),
            id="tableSnippet",
            width="100%",
            padding_left="100px",
            padding_right="100px",
        ),
    )

def barchart_snippet() -> rx.Component:
    queries = rx.foreach(
            State.barchart_queries,
            lambda item, idx: rx.vstack(
                    rx.text('Query'),
                    rx.code_block(
                        item["query"],
                        language="cypher",
                        show_line_numbers=True,
                    ),
                    rx.text('Result'),
                    rx.code_block(
                        item["result"],
                        language="json",
                        show_line_numbers=True,
                    ),
                    font_size="10pt",
                    padding_left="10px",
                    padding_right="10px"
                ),
            )

    drawer = rx.drawer.root(
        rx.drawer.trigger(
            rx.button(rx.icon(tag='message_circle_question'))
        ),
        rx.drawer.overlay(z_index='5'),
        rx.drawer.portal(
            rx.drawer.content(
                rx.scroll_area(
                    queries,
                    width="50em",
                    scrollbars='horizontal'
                ),
                width="50em",
                height="100%",
                left="auto",
                top="auto",
                background_color="#FFF"
            ),
        ),
        direction='right'
    )

    return rx.cond(
        State.barchart_data,
        rx.vstack(
            rx.card(
                rx.vstack(
                    rx.hstack(rx.text(''), rx.spacer(), drawer, align="end"),
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key=State.barchart_yaxis
                        ),
                        rx.recharts.x_axis(data_key=State.barchart_xaxis),
                        rx.recharts.y_axis(),
                        data=State.barchart_data,
                        width="100%"
                    )
                    # 
                ),
                vertical_align="top",
                width="100%",
            ),
            id="barchartSnippet",
            width="100%",
            padding_left="100px",
            padding_right="100px",
        ),
    )
