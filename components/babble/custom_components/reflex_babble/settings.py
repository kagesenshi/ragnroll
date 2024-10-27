from pydantic_settings import BaseSettings
from typing import Optional, Literal

class Settings(BaseSettings):

    OLLAMA_HOST: Optional[str] = None
    OLLAMA_MODEL: str = 'mistral-nemo:12b-instruct-2407-q4_K_M'
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = 'gpt-3.5-turbo'

settings = Settings()