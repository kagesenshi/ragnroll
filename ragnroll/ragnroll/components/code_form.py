import reflex as rx
from reflex_monaco import MonacoEditor
import typing
import enum
import aiohttp
import rxconfig
import json
import yaml

def api_url(link: str):
    if link.startswith('/'):
        return f'{rxconfig.config.api_url}{link}'
    if '://' in link:
        return link
    return f'{rxconfig.config.api_url}/{link}'

class Resource(typing.TypedDict):
    title: str
    link: str 

class Operation(enum.StrEnum):

    CREATE: str = 'create'
    UPDATE: str = 'update'

class EditorState(rx.State):

    resources: list[Resource] = [] 
    title: str  = 'default'
    resource_url: str 
    create_url: str
    code: str = ''
    operation: Operation = Operation.CREATE

    def create_form(self):
        self.operation = Operation.CREATE
        self.code = ''

    @rx.var
    def page_title(self):
        if self.operation == Operation.CREATE:
            return "Create New"
        return "Editing : %s" % self.title

    async def configure(self, url: str):
        async with aiohttp.ClientSession() as client:
            resp = await client.get(api_url(url))
            resources = await resp.json()

        self.create_url = url
        self.resources = [
            Resource(title=r['data']['title'], link=r['links']['self']) for r in resources['data']
        ]

    async def load_resource(self, url: str, operation: Operation = Operation.UPDATE):
        async with aiohttp.ClientSession() as client:
            resp = await client.get(api_url(url))
            resource = await resp.json()

        self.title = resource['data']['metadata']['title'] or resource['data']['metadata']['name']
        self.code = yaml.safe_dump(resource['data'], indent=4)
        self.resource_url = url
        self.operation = operation

    async def submit_create(self):
        code = yaml.safe_load(self.code)
        async with aiohttp.ClientSession() as client:
            resp = await client.post(api_url(self.create_url), json=code)
            out = await resp.json()
            status = resp.status

        if status == 200:
            self.code = ''
            yield rx.toast.success('Create successful')
        else:
            yield rx.toast.error('Create failed. %s' % json.dumps(out))

    async def submit_update(self):
        code = yaml.safe_load(self.code)
        async with aiohttp.ClientSession() as client:
            resp = await client.post(api_url(self.resource_url), json=code)
            out = await resp.json()
            status = resp.status

        if status == 200:
            self.code = ''
            yield rx.toast.success('Update successful')
        else:
            yield rx.toast.error('Update failed. %s' % out['detail'])


        

    
        
def resource_link(title, link):
    return rx.link(
        rx.card(rx.text(title), width='100%'),
        href='#',
        on_click=lambda : EditorState.load_resource(link),
        width="100%",
    )

def editor():
    return MonacoEditor(value=EditorState.code, language='yaml', theme='vs-dark', width='100%', height='80vh')

def code_form(**kwargs):
    return rx.hstack(
        rx.vstack(
            rx.flex(
                rx.button(rx.icon('plus'), rx.text('Add New'), on_click=lambda: EditorState.create_form),
                rx.foreach(EditorState.resources, lambda r: resource_link(r['title'], r['link'])),
                direction='column',
                width="100%"
            ), 
            width="20%",
            on_mount=EditorState.configure('/resource/expertise/v1/')
        ),
        rx.vstack(
            rx.vstack(
                rx.hstack(
                    rx.hstack(rx.text(EditorState.page_title)), 
                    rx.hstack(
                        rx.cond(
                            EditorState.operation == Operation.CREATE, 
                            rx.button('Create', on_click=EditorState.submit_create),                            
                        ),
                        rx.cond(
                            EditorState.operation == Operation.UPDATE,
                            rx.button('Save', on_click=EditorState.submit_update)
                        ),
                        justify='end'
                    ), 
                    width='100%',
                    justify='between',
                    align_items='center'
                ), 
                editor(), 
                width='100%', 
                ), 
            width="80%"
        ),
        padding="20px",
        width="100%"
    )
