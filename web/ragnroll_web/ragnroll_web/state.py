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

class RouteVars(rx.State):
    @rx.var
    def node_id(self) -> str:
        return self.router.page.params.get("node_id", None)

class SnippetQuery(typing.TypedDict):
    query: str
    result: str


class QuestionCRUD(rx.State):
    prev_url: typing.Optional[str]
    next_url: typing.Optional[str]
    current_url: str
    current_page: int
    data: list[dict[str, typing.Any]] = []
    columns: list[dict[str,str]] = []
    reloading: bool = False

    @rx.var
    def node_id(self) -> str:
        return self.router.page.params.get("node_id", None)


    async def dialog_on_open_change(self, is_open: bool):
        if not is_open:
            async for i in self.refresh():
                yield i 
 
    async def refresh(self):
        self.reloading = True
        print(self.node_id)
        self.current_url = f'{settings.BACKEND_URI}/retrieval_query/{self.node_id}/question'
        yield
        self.columns = [{'name': 'id', 'title':'ID'}, {'name': 'question', 'title':'Question'}]
        async with httpx.AsyncClient(timeout=10.0) as client:
            print(self.current_url)
            response = await client.get(self.current_url)
            data = response.json()
            print(data)
        self.data = [{'id': r['id'], 'question': r['properties']['question']} for r in data['data']]
        self.reloading = False
        self.prev_url = None
        self.next_url = None
        yield

    async def enter_next_page(self):
        pass

    async def enter_prev_page(self):
        pass

    async def create(self, form_data: dict):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f'{settings.BACKEND_URI}/retrieval_question', json={
                'question': form_data['question']
            })
            data = response.json()
            question_node_id = data['id']

            response = await client.post(f'{settings.BACKEND_URI}/retrieval_query/{self.node_id}/question', json={
                'node_id': question_node_id
            })
            data = response.json()
            print(data)
        async for i in self.refresh():
            yield i 

    async def delete(self, node_id):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f'{settings.BACKEND_URI}/retrieval_question/{node_id}')
            data = response.json()
        async for i in self.refresh():
            yield i

class QueryCRUD(rx.State):
    prev_url: str
    next_url: str
    current_url: str
    current_page: int
    data: list[dict[str, typing.Any]] = []
    columns: list[dict[str,str]] = []
    reloading: bool = False


    async def dialog_on_open_change(self, is_open: bool):
        if not is_open:
            async for i in self.refresh():
                yield i 
 
    async def refresh(self):
        self.reloading = True
        if not self.current_url:
            self.current_url = f'{settings.BACKEND_URI}/retrieval_query?page_size=10'
        yield
        self.columns = [{'name': 'id', 'title':'ID'}, {'name': 'query', 'title':'Query'}]
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.current_url)
            data = response.json()
            print(data)
        self.data = [{'id': r['id'], 'query': r['properties']['query']} for r in data['data']]
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

    async def create(self, form_data: dict):
        query = form_data['query']
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f'{settings.BACKEND_URI}/retrieval_query', json={'query': query})
            data = response.json()
        async for i in self.refresh():
            yield i       

    async def delete(self, node_id):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f'{settings.BACKEND_URI}/retrieval_query/{node_id}')
            data = response.json()
        async for i in self.refresh():
            yield i


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
    
    async def handle_submit(self, form_data: dict):
        if self.searching:
            return 
        yield 
        self.summary = None
        self.alert_message = None
        self.searching = True
        self.snippet = None
        self.snippet_queries = []
        yield
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(f'{settings.BACKEND_URI}/search', params={'question': form_data['question']})
                data = response.json()
            self.snippet = data['meta']['snippet']
            self.snippet_queries = data['meta']['queries']
            print("Snippet: ", data)
        except httpx.ReadTimeout:
            self.alert_message = "Backend timeout"
        except httpx.ConnectError:
            self.alert_message = "Unable to connect to backend"
        finally:
            self.searching=False
            yield

Session = State