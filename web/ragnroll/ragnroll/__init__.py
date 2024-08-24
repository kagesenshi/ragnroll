import logging
import pydantic

log = logging.getLogger("ragdemo")

class Settings(pydantic.BaseSettings):

    BACKEND_URI: str = "http://localhost:5000"

settings = Settings()