import fastapi
import pydantic 
from .model import RetrievalStrategy, Document
from . import db
import neo4j
import typing
import urllib.parse

app = fastapi.FastAPI(title="RAG'n'Roll")

class ItemLinks(pydantic.BaseModel):
    self: pydantic.HttpUrl
    
class NodeMeta(pydantic.BaseModel):
    id: int
    labels: list[str]
    links: ItemLinks
   
class RetrievalStrategyItem(NodeMeta):
    properties: RetrievalStrategy

class ItemListMeta(pydantic.BaseModel):
    total_items: typing.Optional[int] = None
    current_page: typing.Optional[int] = None
    page_size: typing.Optional[int] = None
    total_pages: typing.Optional[int] = None

class ItemListLinks(pydantic.BaseModel):
    first_page: typing.Optional[pydantic.AnyHttpUrl] = None
    prev_page: typing.Optional[pydantic.AnyHttpUrl] = None
    next_page: typing.Optional[pydantic.AnyHttpUrl] = None
    final_page: typing.Optional[pydantic.AnyHttpUrl] = None

class RetrievalStrategyItemList(pydantic.BaseModel):
    data: list[RetrievalStrategyItem]
    meta: ItemListMeta
    links: ItemListLinks

class SearchParam(pydantic.BaseModel):
    query: str

class SearchData(pydantic.BaseModel):
    title: str
    match: str
    url: pydantic.AnyHttpUrl

class SearchMeta(pydantic.BaseModel):
    snippet: str

class SearchResult(pydantic.BaseModel):
    data: list[SearchData]
    meta: SearchMeta

class Message(pydantic.BaseModel):
    msg: typing.Optional[str]

# Search
@app.get("/search")
async def search(query: str) -> SearchResult:
    return {
        "data": [],
        "meta": {
            "snippet": query
        }
    }

@app.post("/search")
async def post_search(payload: SearchParam) -> SearchResult:
    return {
        "data": [],
        "meta": {
            "snippet": ''
        }
    }

# RAG Training Data
@app.post("/retrieval_strategy")
async def add_retrieval_strategy(request: fastapi.Request, payload: RetrievalStrategy) -> Message:
    session = await db.session(request)
    collection = db.RetrievalStrategy(session)
    await collection.create(payload)
    return {
        "msg": "success"
    }

@app.get("/retrieval_strategy", name='list_retrieval_strategy', response_model_exclude_none=True)
async def list_retrieval_strategy(request: fastapi.Request, page:int =0, page_size: int=100) -> RetrievalStrategyItemList:
    session = await db.session(request)
    collection = db.RetrievalStrategy(session)
    total_count = await collection.total_count()
    items = await collection.list_all(limit=page_size, offset=page * page_size)
    total_pages = int(total_count / page_size)
    if page > total_pages:
        raise fastapi.HTTPException(404)
    pagemeta = ItemListMeta(page_size=page_size, current_page=page, total_items=total_count, total_pages=total_pages)

    links = ItemListLinks()
    here_url = request.url_for('list_retrieval_strategy')
    links.first_page = '%s?%s' % (here_url, urllib.parse.urlencode({'page': 0, 'page_size': page_size}))
    if total_pages != 0:
        links.final_page = '%s?%s' % (here_url, urllib.parse.urlencode({'page': total_pages, 'page_size': page_size}))
    if page > 0:
        links.prev_page = '%s?%s' % (here_url, urllib.parse.urlencode({'page': page-1, 'page_size': page_size}))
    if page < total_pages:
        links.next_page = '%s?%s' % (here_url, urllib.parse.urlencode({'page': page+1, 'page_size': page_size}))
    result = {
        'data': [
            RetrievalStrategyItem(
                links={'self':str(request.url_for('get_retrieval_strategy', entry_id=item.id))}, 
                                  **item.model_dump())
            for item in items],
        'meta': pagemeta,
        'links': links
    }
    return result

@app.get("/retrieval_strategy/{entry_id}", name='get_retrieval_strategy')
async def get_retrieval_strategy(request: fastapi.Request, entry_id: int) -> RetrievalStrategyItem:
    session = await db.session(request)
    collection = db.RetrievalStrategy(session)
    record = await collection.get(entry_id)
    if not record:
        raise fastapi.HTTPException(404)
    data = record.model_dump()
    data['links'] = ItemLinks(self=str(request.url_for('get_retrieval_strategy', entry_id=record.id)))
    return RetrievalStrategyItem(**data)

@app.delete("/retrieval_strategy/{entry_id}")
async def delete_retrieval_strategy(request: fastapi.Request, entry_id: int) -> Message:
    session = await db.session(request)
    collection = db.RetrievalStrategy(session)
    record = await collection.get(entry_id)
    if not record:
        raise fastapi.HTTPException(404)
    await collection.delete(entry_id)
    return {
        'msg': 'success'
    }

@app.put("/retrieval_strategy/{entry_id}")
async def update_retrieval_strategy(request: fastapi.Request, entry_id: int, payload: RetrievalStrategy) -> RetrievalStrategyItem:
    session = await db.session(request)
    collection = db.RetrievalStrategy(session)
    record = await collection.get(entry_id)
    if not record:
        raise fastapi.HTTPException(404)
    updated = await collection.update(entry_id, payload)
    data = updated.model_dump()
    data['links'] = ItemLinks(self=str(request.url_for('get_retrieval_strategy', entry_id=updated.id)))   
    return data

# Document Management
@app.post("/document")
async def create_document_meta(payload: Document) -> Message:
    return {}

@app.get("/document/{entry_id}")
async def get_document_meta(entry_id: int) -> Document:
    return {}

@app.put("/document/{entry_id}")
async def update_document_meta(entry_id: int, payload: Document) -> Message:
    return {}

@app.delete("/document/{entry_id}")
async def delete_document_meta(entry_id: int) -> Message:
    return {}

@app.put("/document/{entry_id}/file")
async def upload_document(entry_id: int):
    return {}

@app.get("/document/{entry_id}/file")
async def download_document(entry_id: int):
    return {}
