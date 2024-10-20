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
    from .page import search
    from .page import expertise
    from .page import graph
    router.reflex_app.api.include_router(router.router)

load()

