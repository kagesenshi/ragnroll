import fastapi
import pydantic 
from . import model
from . import db
import neo4j
import typing
import urllib.parse
from .view import CollectionView

app = fastapi.FastAPI(title="RAG'n'Roll")

# Search
@app.get("/search")
async def search(query: str) -> model.SearchResult:
    return {
        "data": [],
        "meta": {
            "snippet": query
        }
    }

@app.post("/search")
async def post_search(payload: model.SearchParam) -> model.SearchResult:
    return {
        "data": [],
        "meta": {
            "snippet": ''
        }
    }

async def retrieval_strategy_view(request: fastapi.Request):
    session = await db.session(request)
    collection = db.RetrievalStrategy(session)
    view = CollectionView[model.RetrievalStrategy](request, collection, 
                          'list_retrieval_strategy', 
                          'create_retrieval_strategy', 'read_retrieval_strategy',
                          'update_retrieval_strategy', 'delete_retrieval_strategy')
    return view

# RAG Training Data
@app.post("/retrieval_strategy", name='create_retrieval_strategy')
async def create_retrieval_strategy(request: fastapi.Request, payload: model.RetrievalStrategy) -> model.Message:
    view = await retrieval_strategy_view(request) 
    return await view.create(payload)

@app.get("/retrieval_strategy", name='list_retrieval_strategy', response_model_exclude_none=True)
async def list_retrieval_strategy(request: fastapi.Request, page:int =0, page_size: int=100) -> model.ItemList[model.RetrievalStrategy]:
    view = await retrieval_strategy_view(request)
    res= await view.list_all(page, page_size)
    return res

@app.get("/retrieval_strategy/{entry_id}", name='read_retrieval_strategy')
async def get_retrieval_strategy(request: fastapi.Request, entry_id: int) -> model.NodeItem[model.RetrievalStrategy]:
    view = await retrieval_strategy_view(request)
    return await view.get(entry_id)

@app.put("/retrieval_strategy/{entry_id}", name='update_retrieval_strategy')
async def update_retrieval_strategy(request: fastapi.Request, entry_id: int, payload: model.RetrievalStrategy) -> model.NodeItem[model.RetrievalStrategy]:
    view = await retrieval_strategy_view(request)
    return await view.update(entry_id, payload)

@app.delete("/retrieval_strategy/{entry_id}", name='delete_retrieval_strategy')
async def delete_retrieval_strategy(request: fastapi.Request, entry_id: int) -> model.Message:
    view = await retrieval_strategy_view(request)
    return await view.delete(entry_id)

# Document Management
@app.post("/document")
async def create_document_meta(payload: model.Document) -> model.Message:
    return {}

@app.get("/document/{entry_id}")
async def get_document_meta(entry_id: int) -> model.Document:
    return {}

@app.put("/document/{entry_id}")
async def update_document_meta(entry_id: int, payload: model.Document) -> model.Message:
    return {}

@app.delete("/document/{entry_id}")
async def delete_document_meta(entry_id: int) -> model.Message:
    return {}

@app.put("/document/{entry_id}/file/{property}")
async def upload_document(entry_id: int, property: str):
    return {}

@app.get("/document/{entry_id}/file/{property}")
async def download_document(entry_id: int, property: str):
    return {}

