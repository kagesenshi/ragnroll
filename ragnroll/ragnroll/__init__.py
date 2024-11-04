"""Base template for Reflex."""
import logging
import pydantic
import pydantic_settings
import reflex
from rxconfig import config 
from .ragnroll import app

log = logging.getLogger("ragnroll")

def load():
    from .backend import router 
    from .backend.endpoint import search 
    from .backend.endpoint.resource import expertise 
    from .backend.endpoint import chat as chat
    from .backend.config import settings
    for r in router.reflex_app.api.routes:
        if r.path in ['/docs', '/openapi.json']:
            router.reflex_app.api.routes.remove(r)
    router.reflex_app.api.include_router(router.router)
    router.reflex_app.api.swagger_ui_init_oauth = {
        'appName': "RAG'n'Roll"
    }
    router.reflex_app.api.setup()

load()


