import reflex as rx

from ragnroll import state
from ragnroll.components import navbar
import reflex_chakra as rxchakra

def main_template(component: rx.Component, **kwargs):
    return rx.vstack(
        navbar(),
        # alert box
        rx.cond(
            state.Session.alert_message,
            rxchakra.alert(
                rxchakra.alert_icon(),
                rxchakra.alert_title(state.Session.alert_message),
                status="error",
            ),
        ),
        rx.vstack(component, width="100%", padding_left="20px", padding_right="20px"),
        width="100%",
        **kwargs
    )