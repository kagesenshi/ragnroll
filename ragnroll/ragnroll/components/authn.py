from .oidc import oidc_auth_provider
from ..backend.config import settings
from ..backend.authn import oidc_configuration, decode_token
from ..backend.exc import Unauthorized
from rxconfig import config 
import httpx
import reflex as rx
import jwt
import traceback
import sys
import asyncio

class AuthState(rx.State):

    access_token: str = rx.Cookie(name='access_token')
    id_token: str = rx.Cookie(name='id_token')
    refresh_token: str = rx.Cookie(name='refresh_token')
    token_type: str = rx.Cookie(name='token_type')

    logged_in: bool = False

    @rx.var
    def authorization_header(self):
        return f'{self.token_type or "Bearer"} {self.id_token}'

class State(rx.State):

    async def on_success(self, result: dict):
        async with httpx.AsyncClient() as client:
            resp = await client.post(oidc_configuration.token_endpoint, data={
                'grant_type': 'authorization_code',
                'code': result['code'],
                'scope': result['scope'],
                'client_id': settings.OIDC_CLIENT_ID,
                'client_secret': settings.OIDC_CLIENT_SECRET,
                'redirect_uri': config.deploy_url + '/oauth2-redirect'
            })
            tokens = resp.json()
            if resp.status_code != 200:
                message = "Unable to get auth token from authorization code"
                yield rx.toast.error(message)
                raise Unauthorized(message)
            auth: AuthState = await self.get_state(AuthState)
            auth.access_token = tokens['access_token']
            auth.id_token = tokens['id_token']
            auth.token_type = tokens['token_type']
            auth.refresh_token = tokens['refresh_token']
        yield rx.toast.success("Login successful")
        yield self.__class__.refresh

    async def on_failure(self, error: str):
        yield rx.toast.error(error)

    @rx.background
    async def refresh(self):
        async with self:
            auth: AuthState = await self.get_state(AuthState)
            refresh_token = auth.refresh_token
            if not auth.refresh_token:
                auth.logged_in = False
            try:
                decoded = decode_token(auth.id_token)
                auth.logged_in = True
            except jwt.ExpiredSignatureError:
                print('token expired')
                auth.logged_in = False
                pass
            except jwt.PyJWTError as e:
                traceback.print_exc(file=sys.stderr)
                auth.logged_in = False
                raise e
            logged_in = auth.logged_in

        if logged_in:
            if settings.DEBUG:
                print('next refresh')
            await asyncio.sleep(60)
            yield self.__class__.refresh
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(oidc_configuration.token_endpoint, data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': settings.OIDC_CLIENT_ID,
                'client_secret': settings.OIDC_CLIENT_SECRET,
            })
            tokens = resp.json()
            if resp.status_code != 200:
                message = "Unable to refresh auth token"
                yield rx.toast.error(message)
                raise Unauthorized(message)
            print('token refreshed')

            async with self:
                auth: AuthState = await self.get_state(AuthState)
                auth.access_token = tokens['access_token']
                auth.id_token = tokens['id_token']
                auth.token_type = tokens['token_type']
                try:
                    decoded = decode_token(auth.id_token)
                except jwt.PyJWTError as e:
                    self.logged_in = False
                    yield
                    raise e
                auth.logged_in = True



    async def on_mount(self):
        yield self.__class__.refresh

@rx.page('/oauth2-redirect')
def oauth2_redirect() -> rx.Component:
    return rx.script("window.close('','_parent','')")


def login_button() -> rx.Component:
    return oidc_auth_provider(client_id=settings.OIDC_CLIENT_ID, authorization_url=oidc_configuration.authorization_endpoint, 
                               redirect_uri=config.deploy_url + '/oauth2-redirect', 
                               scope='openid profile email',
                               on_success=State.on_success,
                               on_failure=State.on_failure,
                               response_type='code',
                               extra_params={'prompt':'select_account', 'access_type': 'offline'},
                               on_mount=State.on_mount.debounce(100))

def login_page() -> rx.Component:
    return rx.flex(
            rx.card(
               rx.vstack(
                    rx.heading(config.app_title),
                    rx.divider(),
                    login_button(),
                    align='center'
               ),
               padding="1em 3em"
            ),
              justify='center',
              align='center',
              height="800px"
    )

def httpx_auth(token_type, token):
    def _httpx_auth(request):
        request.headers['Authorization'] = f'{token_type} {token}'
        return request
    return httpx._auth.FunctionAuth(_httpx_auth)