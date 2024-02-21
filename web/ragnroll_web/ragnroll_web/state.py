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

class State(rx.State):
    """The app state."""
    
    drawer_open: bool = False # Whether the drawer is open.
    searching: bool = False 
    username: str
    password: str
    search_input: str = ""
    valid_input: bool = True
    
    is_result_empty: bool = True
    search_result_list: List[Dict[str, str]] = []
    
    intent_results = []
    intent_type: str = ""
    
    api_data: str = ""
    has_summary: bool = False
    summary: str = ""
    state_response = []
    query: str = ''
    has_kp: bool = False
    cafe_name: str = ''
    cafe_city: str = ''
    cafe_rating: str = ''
    cafe_rateForTwo: str = ''
    alert_message: str = ""
    
    def toggle_drawer(self):
        self.drawer_open = not self.drawer_open
    
    async def handle_enter(self, key):
        if key == 'Enter':
            async for i in self.handle_submit():
                pass

    async def handle_submit(self):
        if self.searching:
            return 
        self.searching = True
        yield
        await asyncio.sleep(4)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f'{settings.BACKEND_URI}/search', params={'question': self.query})
            data = response.json()

        self.searching=False
        yield
        self.summary = data['meta']['snippet']

    
