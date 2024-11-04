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

class State(rx.State):

    access_token: str = rx.Cookie(name='access_token')
    id_token: str = rx.Cookie(name='id_token')
    refresh_token: str = rx.Cookie(name='refresh_token')
    token_type: str = rx.Cookie(name='token_type')

    logged_in: bool = False

    @rx.var
    def authorization_header(self):
        return f'{self.token_type or "Bearer"} {self.id_token}'

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
            self.access_token = tokens['access_token']
            self.id_token = tokens['id_token']
            self.token_type = tokens['token_type']
            self.refresh_token = tokens['refresh_token']
        yield rx.toast.success("Login successful")
        yield self.__class__.refresh

    async def on_failure(self, error: str):
        yield rx.toast.error(error)

    async def refresh(self):
        if not self.refresh_token:
            self.logged_in = False
            print('no refresh token')
            return 
        try:
            decoded = decode_token(self.id_token)
            self.logged_in = True
            print('logged in')
            return 
        except jwt.ExpiredSignatureError:
            print('token expired')
            pass
        except jwt.PyJWTError as e:
            traceback.print_exc(file=sys.stderr)
            raise e
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(oidc_configuration.token_endpoint, data={
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': settings.OIDC_CLIENT_ID,
                'client_secret': settings.OIDC_CLIENT_SECRET,
            })
            tokens = resp.json()
            if resp.status_code != 200:
                message = "Unable to refresh auth token"
                yield rx.toast.error(message)
                raise Unauthorized(message)
            print('token refreshed')
            self.access_token = tokens['access_token']
            self.id_token = tokens['id_token']
            self.token_type = tokens['token_type']
            try:
                decoded = decode_token(self.id_token)
            except jwt.PyJWTError as e:
                self.logged_in = False
                yield
                raise e

        self.logged_in = True

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