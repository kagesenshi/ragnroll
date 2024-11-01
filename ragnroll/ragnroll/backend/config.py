import pydantic_settings
import typing

class Settings(pydantic_settings.BaseSettings):

    NEO4J_URI: str
    NEO4J_DATABASE: str
    NEO4J_USERNAME: typing.Optional[str]
    NEO4J_PASSWORD: typing.Optional[str]
    NEO4J_USE_SSL: bool = False
    NEO4J_SSL_CA_CERT: typing.Optional[str] = ''
    NEO4J_USE_BEARER_TOKEN: bool = False
    OPENAI_API_KEY: str
    DEBUG: bool = False
    ALLOW_FALLBACK: bool = True
    AUTHN_METHOD: typing.Optional[typing.Literal['oidc', 'dummy']] = None
    OIDC_CLIENT_ID: typing.Optional[str] = None
    OIDC_CLIENT_SECRET: typing.Optional[str] = None
    OIDC_DISCOVERY_URL: typing.Optional[str] = None

settings = Settings()