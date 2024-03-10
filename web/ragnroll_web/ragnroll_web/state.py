import reflex as rx
import time
import asyncio
import httpx
import json
import re
from typing import List
from typing import Dict
import traceback
from . import log
from . import settings
import typing
import asyncio

class SnippetQuery(typing.TypedDict):
    query: str
    result: str

class CRUD(rx.State):
    prev_url: str
    next_url: str
    current_url: str
    current_page: int
    data: list[dict[str, typing.Any]] = []
    columns: list[dict[str,str]] = []
    reloading: bool = False

class QuestionCRUD(CRUD):

    async def dialog_on_open_change(self, is_open: bool):
        if not is_open:
            async for i in self.refresh():
                yield i 
 
    async def refresh(self):
        self.reloading = True
        if not self.current_url:
            self.current_url = f'{settings.BACKEND_URI}/retrieval_question?page_size=10'
        yield
        self.columns = [{'name': 'id', 'title':'ID'}, {'name': 'question', 'title':'Question'}]
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.current_url)
            data = response.json()
            print(data)
        self.data = [{'id': r['id'], 'question': r['properties']['question']} for r in data['data']]
        self.current_page = data['meta']['current_page'] + 1
        self.next_url = data['links'].get('next_page')
        self.prev_url = data['links'].get('prev_page')
        self.reloading = False
        yield

    async def enter_next_page(self):
        self.current_url = self.next_url
        async for i in self.refresh():
            yield i

    async def enter_prev_page(self):
        self.current_url = self.prev_url
        async for i in self.refresh():
            yield i

class QuestionCreateForm(rx.State):
    
    question: str

    async def submit(self):
        await asyncio.sleep(1) # wait for debounce
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f'{settings.BACKEND_URI}/retrieval_question', json={'question': self.question})
            data = response.json()

class State(rx.State):
    """The app state."""
    
    drawer_open: bool = False # Whether the drawer is open.
    searching: bool = False 
    search_input: str = ""
    
    is_result_empty: bool = True
    search_result_list: List[Dict[str, str]] = []
    
    snippet: typing.Optional[str] = ""
    snippet_queries: list[dict[str, str]] = []
    query: str = ''
    has_kp: bool = False
    alert_message: str = ""
    
    def toggle_drawer(self):
        self.drawer_open = not self.drawer_open
    
    async def handle_enter(self, key):
        if key == 'Enter':
            async for i in self.handle_submit():
                yield

    async def handle_submit(self):
        if self.searching:
            return 
        yield rx.redirect('/')
        self.summary = None
        self.alert_message = None
        self.searching = True
        self.snippet = None
        self.snippet_queries = []
        yield
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f'{settings.BACKEND_URI}/search', params={'question': self.query})
                data = response.json()
            self.snippet = data['meta']['snippet']
            self.snippet_queries = data['meta']['queries']
            print("Snippet: ", data)
        except httpx.ReadTimeout:
            yield
        except httpx.ConnectError:
            self.alert_message = "Unable to connect to backend"
        finally:
            self.searching=False
            yield

Session = State