import logging
import pydantic
import pydantic_settings

log = logging.getLogger("ragdemo")

class Settings(pydantic_settings.BaseSettings):

    BACKEND_URI: str = "http://localhost:8000"

settings = Settings()