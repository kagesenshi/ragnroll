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

class SnippetQuery(typing.TypedDict):
    query: str
    result: str

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
        self.summary = None
        self.alert_message = None
        self.searching = True
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


    
