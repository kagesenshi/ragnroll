import reflex as rx
import httpx
from . import settings
import typing
import asyncio

class SearchResultItem(rx.Base):
    data: list[dict[str, typing.Any]]
    queries: list[dict[str,str]]
    fields: list[str]
    visualization: str
    axes: dict[str, str] = {}
 

class State(rx.State):
    """The app state."""
    
    searching: bool = False 
    search_results: list[SearchResultItem] = [] 
    query: str = ''
    alert_message: str = ""
    
    async def handle_submit(self, form_data: dict):
        if self.searching:
            return 
        yield 
        self.summary = None
        self.alert_message = None
        self.searching = True
        yield
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(f'{settings.API_URL}/search', params={'question': form_data['question']})
                data = response.json()
            self.search_results = [SearchResultItem(**d) for d in data['data']]
        except httpx.ReadTimeout:
            self.alert_message = "Backend timeout"
        except httpx.ConnectError:
            self.alert_message = "Unable to connect to backend"
        finally:
            self.searching=False
            yield

Session = State