import typing
from .config import settings

def load():
    from . import router 
    from .endpoint import search 
    from .endpoint.resource import expertise 

    router.reflex_app.api.include_router(router.router)

load()

