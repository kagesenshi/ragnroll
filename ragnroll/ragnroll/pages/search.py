import reflex as rx
import reflex_chakra as rxchakra
from ..templates import template
from ..views.search import SearchState, SearchResultItem
from ..components.snippet.text import text_snippet
from ..components.snippet.barchart import barchart_snippet
from ..components.snippet.table import table_snippet


def render_snippet(item: SearchResultItem):
    return rx.match(item.visualization,
        ('text-answer', text_snippet(item)),
        ('table', table_snippet(item)),
        ('bar-chart', barchart_snippet(item)),
        rx.text("Unsupported visualization : ", item.visualization)
    )


def wrap_search(component: rx.Component) -> rx.Component:
    return rx.cond(
        SearchState.searching,
        rx.flex(
            rx.center(
                rxchakra.spinner(size='xl'),
                width='100%'
            ),
            width="100%",
            height="200px"
        ),
        component,
    )




@template(route='/', title='Search')
def index() -> rx.Component:
    return rx.vstack(
            rx.form(
                rx.vstack(
                    rx.flex(
                        rx.spacer(),
                        rx.center(
                            rx.input(
                                placeholder="Search here ...",
                                size="3",
                                width="30em",
                                name="question",
                            ),
                            rx.button(rx.icon(tag="search"), size="3"),
                            spacing="2",
                        ),
                        rx.spacer(),
                        width="100%",
                    )
                ),
                on_submit=SearchState.handle_submit,
                width="100%",
            ),
            wrap_search(
                rx.vstack(
                    rx.cond(
                        SearchState.search_results,
                        rx.foreach(SearchState.search_results, render_snippet),
                        rx.text("No search results"),
                    ),
                    width="100%",
                )
            ),
            width="100%",
        )