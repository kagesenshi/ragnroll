import fastapi
import pydantic 
from . import model
from . import db
import neo4j
import neo4j.exceptions
import typing
import urllib.parse
from . import prompt
from .crud.view import CollectionView
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages.base import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import GraphCypherQAChain
from langchain.chains.graph_qa.cypher import extract_cypher
from langchain_community.graphs import Neo4jGraph
import json
import asyncio

app = fastapi.FastAPI(title="RAG'n'Roll")

async def retrieval_strategy(request: fastapi.Request) -> db.RetrievalStrategy:
    session = await db.session(request)
    chat = ChatOpenAI()
    embedding = OpenAIEmbeddings()
    collection = db.RetrievalStrategy(session, chat, embedding)
    return collection
   
async def retrieval_strategy_view(request: fastapi.Request):
    collection = await retrieval_strategy(request)
    view = CollectionView[model.RetrievalStrategy](request, collection, 
                          'list_retrieval_strategy', 
                          'create_retrieval_strategy', 'read_retrieval_strategy',
                          'update_retrieval_strategy', 'delete_retrieval_strategy')
    return view


async def _search(request: fastapi.Request, question: str):
    collection = await retrieval_strategy(request)
    matches = await collection.match_question(question)
    matches = [{'question': m.properties.question, 'query': m.properties.query} for m in matches]
    if len(matches):
        chain = prompt.rag_query_generator | collection.chat 
        corrector_chain = prompt.cypher_corrector | collection.chat
        answer_chain = prompt.answer_generator | collection.chat
        qachain = GraphCypherQAChain.from_llm(collection.chat, graph=Neo4jGraph(), verbose=True)
        message: BaseMessage = await chain.ainvoke({'data': '\n\n'.join([json.dumps(match) for match in matches]), 'question': question})
        query = message.content
        snippet = ''
        if query == 'IDONOTKNOW':
            msg: str = await qachain.arun(question)
            snippet = msg
        else:
            driver: neo4j.AsyncDriver = db.connect(request)
            async with driver.session() as session:
                retry = 0
                while retry < 3:
                    try:
                        res = await session.run(f'EXPLAIN {query}')
                        print(await res.single())
                        break
                    except (neo4j.exceptions.CypherSyntaxError) as e:
                        print(e.message)
                        message = await corrector_chain.ainvoke({'query': query, 'error': e.message})
                        query = extract_cypher(message.content)
                        print(query)
                    retry +=1 
                data = await (await session.run(query)).data()
                answer: BaseMessage = await answer_chain.ainvoke({'question': question, 'data': '\n\n'.join([json.dumps(d) for d in data])})
                snippet = answer.content
                        
    else:
        snippet = 'Nothing'

    return {
        "data": [],
        "meta": {
            "snippet": snippet,
            "query": query
        }
    }

# Search
@app.get("/search")
async def search(request: fastapi.Request, question: str) -> model.SearchResult:
    return await _search(request, question)

@app.post("/search")
async def post_search(request: fastapi.Request, payload: model.SearchParam) -> model.SearchResult:
    return await _search(request, payload.question)

# RAG Training Data
@app.post("/retrieval_strategy", name='create_retrieval_strategy')
async def create_retrieval_strategy(request: fastapi.Request, payload: model.RetrievalStrategy) -> model.Message:
    view = await retrieval_strategy_view(request) 
    return await view.create(payload)

@app.get("/retrieval_strategy", name='list_retrieval_strategy', response_model_exclude_none=True, response_model_exclude={'data': {'__all__': {'properties': {'embedding'}}}})
async def list_retrieval_strategy(request: fastapi.Request, page:int =0, page_size: int=100) -> model.ItemList[model.NodeItem[model.RetrievalStrategy]]:
    view = await retrieval_strategy_view(request)
    res= await view.list_all(page, page_size)
    return res

@app.get("/retrieval_strategy/{entry_id}", name='read_retrieval_strategy', response_model_exclude={'properties': {'embedding'}, 'score': True})
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

## Document Management
#@app.post("/document")
#async def create_document_meta(payload: model.Document) -> model.Message:
#    return {}
#
#@app.get("/document/{entry_id}")
#async def get_document_meta(entry_id: int) -> model.Document:
#    return {}
#
#@app.put("/document/{entry_id}")
#async def update_document_meta(entry_id: int, payload: model.Document) -> model.Message:
#    return {}
#
#@app.delete("/document/{entry_id}")
#async def delete_document_meta(entry_id: int) -> model.Message:
#    return {}
#
#@app.put("/document/{entry_id}/file/{property}")
#async def upload_document(entry_id: int, property: str):
#    return {}
#
#@app.get("/document/{entry_id}/file/{property}")
#async def download_document(entry_id: int, property: str):
#    return {}
#
#