import logging
import pydantic
import pydantic_settings
import reflex
from rxconfig import config # type: ignore

config: reflex.Config = config

log = logging.getLogger("ragdemo")

class Settings(pydantic_settings.BaseSettings):

    API_URL: str = config.api_url

settings = Settings()