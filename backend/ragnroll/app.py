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
from langchain.chains.graph_qa.prompts import CYPHER_GENERATION_PROMPT, CYPHER_QA_PROMPT
from langchain.chains.graph_qa.cypher import construct_schema
from langchain_core.runnables.base import RunnableSerializable
from langchain.chains.graph_qa.cypher import extract_cypher
from langchain_core.utils.input import get_colored_text, print_text, get_bolded_text
from langchain_community.graphs import Neo4jGraph
import json
import asyncio
import neo4j.spatial
import neo4j.time
import neo4j.graph

app = fastapi.FastAPI(title="RAG'n'Roll")

class CypherChainOutput(typing.TypedDict):
    query: str 
    result: str
    intermediate_steps: list[dict]

class Neo4jJSONEncoder(json.JSONEncoder):
    def default(self, obj):
#        if isinstance(obj, neo4j.graph.Node):
#            return {'labels': obj.labels, 'properties': dict(obj)}
#        elif isinstance(obj, neo4j.graph.Relationship):
#            return {'type': obj.type, 'properties': dict(obj)}
#        elif isinstance(obj, neo4j.graph.Path):
#            return {'nodes': list(obj.nodes), 'relationships': list(obj.relationships)}
#        elif isinstance(obj, neo4j.spatial.Point):
#            return {'crs': obj.crs, 'coordinates': obj.coordinates}
#        elif isinstance(obj, neo4j.time.Duration):
#            return {'months': obj.months, 'days': obj.days, 'seconds': obj.seconds, 'nanoseconds': obj.nanoseconds}
        if isinstance(obj, neo4j.time.Date):
            return obj.iso_format()
        elif isinstance(obj, neo4j.time.Time):
            return obj.iso_format()
        elif isinstance(obj, neo4j.time.DateTime):
            return obj.iso_format()
        return super().default(obj)

def jsonify_result(data: typing.Any, **kwargs):
    return json.dumps(data, cls=Neo4jJSONEncoder, **kwargs)

async def retrieval_question(request: fastapi.Request) -> db.RetrievalQuestion:
    session = await db.session(request)
    chat = ChatOpenAI()
    embedding = OpenAIEmbeddings()
    collection = db.RetrievalQuestion(session, chat, embedding)
    return collection
   

async def retrieval_question_view(request: fastapi.Request):
    collection = await retrieval_question(request)
    view = CollectionView[model.RetrievalQuestion](request, collection, 
                          'list_retrieval_question', 
                          'create_retrieval_question', 'read_retrieval_question',
                          'update_retrieval_question', 'delete_retrieval_question')
    return view

class QueryCorrector(object):

    def __init__(self, driver: neo4j.AsyncDriver, chain: RunnableSerializable, retries=3) -> None:
        self.chain = chain
        self.driver = driver
        self.retries = retries

    async def __call__(self, query: str):
        async with self.driver.session() as session:
            retry = 0
            while retry < self.retries:
                try:
                    res = await session.run(f'EXPLAIN {query}')
                    return query
                except (neo4j.exceptions.CypherSyntaxError) as e:
                    print(e.message)
                    message: BaseMessage = await self.chain.ainvoke({'query': query, 'error': e.message})
                    query = extract_cypher(message.content)
            retry += 1
        return None

async def _get_snippet(request: fastapi.Request, question:str, result_limit: int = 50):
    collection = await retrieval_question(request)
    answer_chain = CYPHER_QA_PROMPT | collection.chat
    corrector_chain = prompt.cypher_corrector | collection.chat
    generator_chain = CYPHER_GENERATION_PROMPT | collection.chat
    driver: neo4j.AsyncDriver = db.connect(request)
    query_corrector = QueryCorrector(driver, corrector_chain)
    qachain = GraphCypherQAChain.from_llm(collection.chat, graph=Neo4jGraph(), verbose=True, return_intermediate_steps=True, 
        validate_cypher=True)
    query = None 
    matches = await collection.match_question(question, min_score=0.9)
    matches = [{'question': m.properties.question, 'query': m.properties.query, 'score': m.score} for m in matches]
    driver: neo4j.AsyncDriver = db.connect(request)
    if len(matches):
        print_text(get_bolded_text("> Entering intent matcher"), end='\n')
        chain = prompt.rag_query_generator | collection.chat 

        print(matches)
        message: BaseMessage = await chain.ainvoke({'data': '\n\n'.join([
                f"Question: {match['question']}\nQuery: {match['query']}" for match in matches
            ]), 'question': question})
        query = message.content
        if query != 'IDONOTKNOW':
            query = await query_corrector(query)

    if not query:
        query_msg: BaseMessage = await generator_chain.ainvoke({'question': question, 'schema': construct_schema(Neo4jGraph().get_structured_schema, [], [])})
        query = query_msg.content
    print(f'Generated query: {query}')
    query = await query_corrector(query)
    print(f'Corrected query: {query}')
    query = query + f' LIMIT {result_limit} '
    query = await query_corrector(query)
    print(f'Final query: {query}')
    async with driver.session() as session:
        data = await (await session.run(query)).data()
        answer: BaseMessage = await answer_chain.ainvoke({'question': question, 'context': jsonify_result(data)})
        snippet = answer.content
        return {
            'snippet': snippet,
            'queries': [{
                'query': query,
                'result': jsonify_result(data, indent=4)
            }]
        }

async def _search(request: fastapi.Request, question: str):
    collection = await retrieval_question(request)

    entity_chain = prompt.entity_identifier | collection.chat
    driver: neo4j.AsyncDriver = db.connect(request)

    async with driver.session() as session:
        res = await session.run('call db.labels()') 
        labels = [r['label'] for r in (await res.data())]
    possible_entity = await entity_chain.ainvoke({'query': question, 'labels': '\n'.join(labels)})
    print(possible_entity)
    snippet = await _get_snippet(request, question)
    if snippet:
        return {
            "data": [],
            "meta": {
                "snippet": snippet['snippet'],
                "queries": snippet['queries']
            }
        }
    return {
        'data': [],
        'meta': {
            'snippet': None,
            'queries': []
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
@app.post("/retrieval_question", name='create_retrieval_question')
async def create_retrieval_question(request: fastapi.Request, payload: model.RetrievalQuestion) -> model.Message:
    view = await retrieval_question_view(request) 
    return await view.create(payload)

@app.get("/retrieval_question", name='list_retrieval_question', response_model_exclude_none=True, response_model_exclude={'data': {'__all__': {'properties': {'embedding'}}}})
async def list_retrieval_question(request: fastapi.Request, page:int =0, page_size: int=100) -> model.ItemList[model.NodeItem[model.RetrievalQuestion]]:
    view = await retrieval_question_view(request)
    res= await view.list_all(page, page_size)
    return res

@app.get("/retrieval_question/{entry_id}", name='read_retrieval_question', response_model_exclude={'properties': {'embedding'}, 'score': True})
async def get_retrieval_question(request: fastapi.Request, entry_id: int) -> model.NodeItem[model.RetrievalQuestion]:
    view = await retrieval_question_view(request)
    return await view.get(entry_id)

@app.put("/retrieval_question/{entry_id}", name='update_retrieval_question')
async def update_retrieval_question(request: fastapi.Request, entry_id: int, payload: model.RetrievalQuestion) -> model.NodeItem[model.RetrievalQuestion]:
    view = await retrieval_question_view(request)
    return await view.update(entry_id, payload)

@app.delete("/retrieval_question/{entry_id}", name='delete_retrieval_question')
async def delete_retrieval_question(request: fastapi.Request, entry_id: int) -> model.Message:
    view = await retrieval_question_view(request)
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