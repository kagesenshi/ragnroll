import fastapi 
import pydantic
from typing import Annotated, Optional, Dict, cast, Any
from typing_extensions import Doc
from .model import OIDCConfiguration, OIDCAccessToken
from fastapi.openapi.models import OAuth2 as OAuth2Model
from .config import settings
import httpx 
from fastapi.security import OAuth2, OAuth2AuthorizationCodeBearer
from fastapi.security.utils import get_authorization_scheme_param
import jwt
from . import exc
import traceback
from starlette.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED

CONFIG_CACHE = {}

class _Identity(pydantic.BaseModel):
    username: str
    email: str

def get_oidc_configuration() -> OIDCConfiguration:
    config = CONFIG_CACHE.get('oidc-config', None)
    if config:
        return config
    with httpx.Client() as client:
        resp = client.get(settings.OIDC_DISCOVERY_URL)
        if resp.status_code != 200:
            raise exc.RagNRollException("Unable to query OIDC discovery endpoint")
        config = OIDCConfiguration.model_validate(resp.json())
    CONFIG_CACHE['oidc-config'] = config
    return config

oidc_configuration = get_oidc_configuration()

def decode_token(token):
    jwk_client =  jwt.PyJWKClient(oidc_configuration.jwks_uri, cache_keys=True)
    signing_key = jwk_client.get_signing_key_from_jwt(token)
    decoded = jwt.decode(token, key=signing_key.key, algorithms=oidc_configuration.id_token_signing_alg_values_supported, options={'verify_aud': False})
    return decoded

async def _get_token(request: fastapi.Request) -> OIDCAccessToken:
    if not oidc_configuration:
        return None

    decoded = getattr(request.state, 'decoded_token', None)
    if decoded:
        return decoded
    
    authorization = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise exc.Unauthorized("Not authenticated")

    try: 
        decoded = decode_token(token)
    except jwt.InvalidTokenError as e:
        raise exc.Unauthorized("Not authenticated")
    except jwt.InvalidKeyError as e:
        traceback.print_exc()
        raise exc.Unauthorized("Not authenticated")

    token = OIDCAccessToken.model_validate(decoded)
    if not token.sub:
        raise exc.Unauthorized("No sub provided in token")
    if not token.email and token.email_verified:
        raise exc.Unauthorized("No valid email address")
    request.state.decoded_token = token
    return token

class OAuth2IDTokenModel(OAuth2Model):
    tokenName: str = pydantic.Field(default='id_token', alias='x-tokenName')

class BearerScheme(OAuth2AuthorizationCodeBearer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model =  OAuth2IDTokenModel(
            flows=self.model.flows, description=self.model.description,
        )

    async def __call__(self, request: fastapi.Request) -> OIDCAccessToken:
        return await _get_token(request)

if settings.AUTHN_METHOD == 'oidc':
    oidc_scheme = BearerScheme(tokenUrl=oidc_configuration.token_endpoint, authorizationUrl=oidc_configuration.authorization_endpoint,
                               scopes={"openid": "OpenID Connect scope", "profile": "Access profile info", "email": "Access email info"})
    async def get_identity(request: fastapi.Request, token: Annotated[OIDCAccessToken, fastapi.Depends(oidc_scheme)]) -> _Identity:
        return _Identity(username=token.email, email=token.email)
else:
    async def get_identity(request: fastapi.Request) -> _Identity:
        return _Identity(username='testuser', email='testuser@localhost')

Identity = Annotated[_Identity, fastapi.Depends(get_identity)]