from ...state import SearchResultItem
import reflex as rx


def barchart_snippet(result: SearchResultItem) -> rx.Component:
    queries = rx.foreach(
            result.queries,
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
        result.data,
        rx.vstack(
            rx.card(
                rx.vstack(
                    rx.hstack(rx.text(''), rx.spacer(), drawer, align="end"),
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key=result.axes['y']
                        ),
                        rx.recharts.x_axis(data_key=result.axes['x']),
                        rx.recharts.y_axis(),
                        data=result.data,
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