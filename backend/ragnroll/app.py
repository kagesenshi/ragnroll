import fastapi
import pydantic 
from . import model
from .crud import db
import neo4j
import neo4j.exceptions
import typing
import urllib.parse
from . import prompt
from .crud.view import NodeCollectionView
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
    print_text(get_bolded_text(f"> Answering question: {question}"), end='\n')
    collection = await model.RAGQueryEndpoints.factory(request)

    chat = ChatOpenAI()
    embeddings = OpenAIEmbeddings()
    answer_chain = CYPHER_QA_PROMPT | chat 
    corrector_chain = prompt.cypher_corrector | chat
    generator_chain = CYPHER_GENERATION_PROMPT | chat
    driver: neo4j.AsyncDriver = db.connect(request)
    session: neo4j.AsyncSession = driver.session()

    query_corrector = QueryCorrector(driver, corrector_chain)
    qachain = GraphCypherQAChain.from_llm(chat, graph=Neo4jGraph(), verbose=True, return_intermediate_steps=True, 
        validate_cypher=True)

    async def _job(txn: neo4j.AsyncTransaction):
        print_text(get_bolded_text("> Entering embedding calculation"), end='\n')
        embedding = await embeddings.aembed_query(question)
        print_text(get_bolded_text("> Embedding done"), end='\n')
        count = 5
        min_score = 0.9
        cypher = '''
            CALL db.index.vector.queryNodes('ragquestion_embedding', $count, $embedding)
            YIELD node, score
            WITH node, score
               WHERE '_RAGQuestion' in labels(node)
               AND score > $min_score
            MATCH (query:_RAGQuery)-[:ANSWERS]-(node)
            RETURN distinct query, node as question, score
           ''' 
        res = await txn.run(cypher, parameters={'embedding': embedding, 'count': count, 'min_score': min_score})
        return await res.data()
    
    matches = await session.execute_read(_job)
    matches = [{'question': m['query']['query'], 
                'query': m['question']['question'],
                'score': m['score']} for m in matches]
    print(matches)
    query = None
    driver: neo4j.AsyncDriver = db.connect(request)
    if len(matches):
        print_text(get_bolded_text("> Entering intent matcher"), end='\n')
        chain = prompt.rag_query_generator | chat 
        print(matches)
        message: BaseMessage = await chain.ainvoke({'data': '\n\n'.join([
                f"Question: {match['question']}\nQuery: {match['query']}" for match in matches
            ]), 'question': question})
        query = message.content
        if query != 'IDONOTKNOW':
            query = await query_corrector(query)

    if not query:
        print_text(get_bolded_text("> Entering generator chain"), end='\n')
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
    collection = await model.RAGQueryEndpoints.factory(request)
    chat = ChatOpenAI()
    entity_chain = prompt.entity_identifier | chat
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

@model.RAGQueryEndpoints.model_post('/question')
async def add_question(request: fastapi.Request, identifier: int, question_id: model.NodeID) -> model.Message:
        node_id = identifier
        session: neo4j.AsyncSession = await db.session(request)
        async def _job(txn: neo4j.AsyncTransaction):
            params = {'__node_id': node_id,
                      'question_id': question_id.node_id}
            cypher = '''
            MATCH (query:_RAGQuery) WHERE id(query) = $__node_id
            MATCH (question:_RAGQuestion) WHERE id(question) = $question_id
            MERGE (query)-[:ANSWERS]->(question)
            '''
            res = await txn.run(cypher, parameters=params)
            return model.Message(msg='Success')
        return await session.execute_write(_job)

@model.RAGQueryEndpoints.model_get('/question', response_model_exclude_none=True)
async def get_questions(request: fastapi.Request, identifier: int) -> model.ItemList[model.NodeItem[model.RAGQuestion]]:
    node_id = identifier
    session = await db.session(request)
    async def _job(txn: neo4j.AsyncTransaction):
        params = {
            '__node_id': node_id
        }
        query = '''
        MATCH (query:_RAGQuery)-[:ANSWERS]-(question:_RAGQuestion) 
        WHERE id(query) = $__node_id
        RETURN distinct id(question) as identifier, labels(question) as node_labels, question as node
        '''
        res = await txn.run(query=query, parameters=params)
        data = await res.data()
        return model.ItemList[model.NodeItem[model.RAGQuestion]](data=[
            model.NodeItem[model.RAGQuestion](
                id=r['identifier'], 
                labels=r['node_labels'], 
                properties=model.RAGQuestion(question=r['node']['question']),
                links=model.ItemLinks(self=str(request.url_for('read_retrieval_question', identifier=r['identifier'])))
            ) for r in data
            ])
    return await session.execute_read(_job)

model.RAGPatternEndpoints.register_views(app)
model.RAGQuestionEndpoints.register_views(app)
model.RAGQueryEndpoints.register_views(app)