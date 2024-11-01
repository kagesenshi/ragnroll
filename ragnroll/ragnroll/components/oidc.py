import reflex as rx
from typing import Literal, Optional

def on_success_signature(result: dict):
    return [result]

def on_failure_signature(result: str):
    return [result]

class OIDCAuthProvider(rx.Component):

    library = 'react-simple-oauth2-login'
    tag = 'OAuth2Login'
    is_default = True

    authorization_url: rx.Var[str]
    redirect_uri: rx.Var[str]
    client_id: rx.Var[str]
    response_type: rx.Var[Literal['token', 'code']] = 'code'
    scope: rx.Var[str]
    button_text: rx.Var[str] = 'Login'
    class_name: rx.Var[str] = 'rt-reset rt-BaseButton rt-r-size-3 rt-variant-solid rt-Button'
    is_cross_origin: rx.Var[bool] = False
    extra_params: rx.Var[Optional[dict]] = None


    on_success: rx.EventHandler[on_success_signature]
    on_failure: rx.EventHandler[on_failure_signature]

oidc_auth_provider = OIDCAuthProvider.create