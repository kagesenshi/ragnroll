import fastapi 
import pydantic
from typing import Annotated
from .model import OIDCConfiguration, OIDCAccessToken
from .config import settings
import httpx 
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
import jwt
from . import exc
import traceback

CONFIG_CACHE = {}

class _Identity(pydantic.BaseModel):
    username: str
    email: str

async def oidc_configuration(request: fastapi.Request) -> OIDCConfiguration:
    config = CONFIG_CACHE.get('oidc-config', None)
    if config:
        return config
    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.OAUTH_DISCOVERY_URL)
        if resp.status_code != 200:
            raise exc.RagNRollException("Unable to query OIDC discovery endpoint")
        config = OIDCConfiguration.model_validate(resp.json())
    CONFIG_CACHE['oidc-config'] = config
    return config

async def _get_token(request: fastapi.Request) -> OIDCAccessToken:
    oidc_settings = await oidc_configuration(request)
    if not oidc_settings:
        return None

    decoded = getattr(request.state, 'decoded_token', None)
    if decoded:
        return decoded
    
    authorization = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise exc.Unauthorized("Not authenticated")

    jwk_client =  jwt.PyJWKClient(oidc_settings.jwks_uri, cache_keys=True)
    try: 
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        # FIXME: should we really ignore audience claim
        decoded = jwt.decode(token, key=signing_key.key, algorithms=oidc_settings.id_token_signing_alg_values_supported, options={'verify_aud': False})
        
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

class OAuth2Mixin(object):

    async def __call__(self, request: fastapi.Request) -> OIDCAccessToken:
        return await _get_token(request)
    
class PasswordBearerScheme(OAuth2Mixin, OAuth2PasswordBearer):
    pass

async def oauth_get_identity(request: fastapi.Request) -> _Identity:
    token = await _get_token(request)
    return _Identity(username=token.email, email=token.email)

async def get_identity(request: fastapi.Request) -> _Identity:
    return await oauth_get_identity(request)

Identity = Annotated[_Identity, fastapi.Depends(get_identity)]