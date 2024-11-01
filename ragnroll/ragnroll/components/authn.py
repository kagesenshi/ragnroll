from .oidc import oidc_auth_provider
from ..backend.config import settings
from ..backend.authn import oidc_configuration, decode_token

from rxconfig import config 
import httpx
import reflex as rx
import jwt
import traceback

class State(rx.State):

    access_token: str = rx.Cookie(name='access_token')
    id_token: str = rx.Cookie(name='id_token')
    token_type: str = rx.Cookie(name='token_type')

    logged_in: bool = False

    @rx.var
    def authorization_header(self):
        return f'{self.token_type or "Bearer"} {self.id_token}'

    async def reload_states(self):
        #from ..pages.chat import ChatClient
        #chatstate: ChatClient = await self.get_state(ChatClient)
        #async for i in chatstate.load_chats_handler():
        #    yield i
        yield

    async def refresh_token(self):
        if not self.id_token:
            self.logged_in = False
            return 
        try:
            decoded = decode_token(self.id_token)
        except jwt.ExpiredSignatureError as e:
            # FIXME: refresh token, or something
            self.logged_in = False
            return
        except jwt.PyJWTError as e:
            traceback.print_exc()
            self.logged_in = False
            return
        self.logged_in = True
        yield
        async for i in self.reload_states():
            yield i
 
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
            self.access_token = tokens['access_token']
            self.id_token = tokens['id_token']
            self.token_type = tokens['token_type']
        self.logged_in = True
        yield rx.toast.success("Login successful")
        async for i in self.reload_states():
            yield i

    async def on_failure(self, error: str):
        self.logged_in = False
        yield rx.toast.error(error)

@rx.page('/oauth2-redirect')
def oauth2_redirect() -> rx.Component:
	return rx.script("window.close('','_parent','')")


def login_button() -> rx.Component:
    return oidc_auth_provider(client_id=settings.OIDC_CLIENT_ID, authorization_url=oidc_configuration.authorization_endpoint, 
                               redirect_uri=config.deploy_url + '/oauth2-redirect', 
                               scope='openid profile email',
                               on_success=State.on_success,
                               on_failure=State.on_failure,
                               response_type='code')

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