import reflex as rx 
from reflex.event import key_event, input_event
from typing import List, Any

class LoadingIcon(rx.Component):
    """A custom loading icon component."""

    library = "react-loading-icons"
    tag = "SpinningCircles"
    stroke: rx.Var[str]
    stroke_opacity: rx.Var[str]
    fill: rx.Var[str]
    fill_opacity: rx.Var[str]
    stroke_width: rx.Var[str]
    speed: rx.Var[str]
    height: rx.Var[str]

    def get_event_triggers(self) -> dict:
        return {"on_change": lambda status: [status]}


loading_icon = LoadingIcon.create

class ThreeDotsLoadingIcon(rx.Component):
    """A custom loading icon component."""

    library = "react-loading-icons"
    tag = "ThreeDots"
    stroke: rx.Var[str]
    stroke_opacity: rx.Var[str]
    fill: rx.Var[str]
    fill_opacity: rx.Var[str]
    stroke_width: rx.Var[str]
    speed: rx.Var[str]
    height: rx.Var[str]

    def get_event_triggers(self) -> dict:
        return {"on_change": lambda status: [status]}


three_dots_loading_icon = ThreeDotsLoadingIcon.create


class ResizableTextArea(rx.Component):
    library = 'react-textarea-autosize'
    tag = "TextareaAutosize"
    is_default = True

    min_rows: rx.Var[int] = 1
    max_rows: rx.Var[int] = 10
    cache_measurements: rx.Var[bool] = False
    default_value: rx.Var[str] = ""

    on_height_change: rx.EventHandler[input_event]
    on_change: rx.EventHandler[input_event]
    on_input: rx.EventHandler[input_event]
    on_focus: rx.EventHandler[input_event]
    on_blur: rx.EventHandler[input_event]
    #on_key_down: rx.EventHandler[key_event]
    on_key_up: rx.EventHandler[key_event]

    special_props: list[rx.Var] = [rx.Var(_js_expr="onKeyDown={textAreaEnterHandler}")]

    def add_custom_code(self) -> List[str]:
        return ["""
        const textAreaEnterHandler = (event) => {
            // Check if 'Enter' key is pressed and 'Shift' is not held
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault(); // Prevents adding a new line
                const nearestForm = event.target.closest('form');
                if (nearestForm) {
                    const submitButton = nearestForm.querySelector('button[type="submit"]');
                    if (submitButton) {
                        submitButton.click(); // Triggers a click on the submit button
                    }
                }   
            }
        };
        """]

resizable_textarea = ResizableTextArea.create