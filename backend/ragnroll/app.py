import fastapi
import pydantic
import yaml.parser 
from . import model
from . import db
from . import settings
import neo4j
import neo4j.exceptions
import typing
import urllib.parse
from . import prompt
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages.base import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import GraphCypherQAChain
from langchain.chains.graph_qa.prompts import CYPHER_GENERATION_PROMPT, CYPHER_QA_PROMPT
from langchain.chains.graph_qa.cypher import construct_schema
from langchain_core.runnables.base import RunnableSerializable
from langchain.chains.graph_qa.cypher import extract_cypher
from .util import format_text
from langchain_community.graphs import Neo4jGraph
import json
import asyncio
import neo4j.spatial
import neo4j.time
import neo4j.graph
import magic
import yaml
import yaml.parser
import openai
import os

app = fastapi.FastAPI(title="RAG'n'Roll")

S = typing.TypeVar('S', bound=pydantic.BaseModel)
async def extract_model(schema: type[S], request: fastapi.Request) -> S:
    content_type = request.headers.get('Content-Type')
    if content_type.lower() in ['application/yaml', 'text/x-yaml', 'application/x-yaml']:
        config_yaml = (await request.body()).decode('utf-8')
        config_json = json.dumps(yaml.safe_load(config_yaml))
    elif content_type.lower() in ['application/json', 'text/json']:
        config_json = await request.body()
    return schema.model_validate_json(config_json)

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

    def __init__(self, session: neo4j.AsyncSession, chat: ChatOpenAI, retries=3) -> None:
        self.chain = prompt.cypher_corrector | chat 
        self.session = session
        self.retries = retries

    async def __call__(self, query: str):
        retry = 0
        while retry < self.retries:
            try:
                res = await self.session.run(f'EXPLAIN {query}')
                return query
            except (neo4j.exceptions.CypherSyntaxError) as e:
                print(format_text("> Correcting query: ", bold=True))
                print(format_text(query, color='yellow'))
                print(format_text(e.message, color='red'))
                message: BaseMessage = await self.chain.ainvoke({'query': query, 'error': e.message})
                query = extract_cypher(message.content)
            retry += 1
        return None

class QuerySample(pydantic.BaseModel):
    question: str 
    query: str
    visualization: model.VisualizationType
    score: float

async def find_queries(session: neo4j.AsyncSession,
                        embedding: list[float], 
                        visualization: model.VisualizationType = model.VisualizationType.TEXT_ANSWER) -> list[QuerySample]:
    async def _job(txn: neo4j.AsyncTransaction):
        count = 5
        min_score = 0.9
        cypher = '''
            CALL db.index.vector.queryNodes('ragquestion_embedding', $count, $embedding)
            YIELD node, score
            WITH node, score
               WHERE '_RAGQuestion' in labels(node)
               AND score > $min_score
            MATCH (query:_RAGQuery)-[:ANSWERS]-(node)
            WHERE query.output_type = $visualization
            RETURN distinct query, node as question, score
           ''' 
        res = await txn.run(cypher, parameters={'embedding': embedding, 'count': count, 
                                                'min_score': min_score, 'visualization': visualization
                                                })
        return await res.data()
    
    matches = await session.execute_read(_job)
    matches = [QuerySample(question=m['question']['question'], 
                query=m['query']['query'],
                visualization=visualization,
                score=m['score']) for m in matches]
    return matches

async def _generate_query_from_sample(session: neo4j.AsyncSession, chat: ChatOpenAI, question: str, 
                                      samples: list[QuerySample]):
    print(format_text("> Entering intent based query generator", bold=True))
    print(format_text("> Sample queries:", bold=True))
    for s in samples:
        print(format_text(s.query, color='yellow'))
    chain = prompt.rag_query_generator | chat 
    message: BaseMessage = await chain.ainvoke({'data': '\n\n'.join([
            f"Question: {sample.question}\nQuery: {sample.query}" for sample in samples
        ]), 'question': question})
    query = message.content
    if query != 'IDONOTKNOW':
        query_corrector = QueryCorrector(session, chat=chat)
        query = await query_corrector(query)
    else:
        return None
    print(format_text(f"> Generated query:", bold=True))
    print(format_text(query, color='yellow'))
    return query

async def _answer_question(request: fastapi.Request, question:str, result_limit: int = 50,
                        visualization: model.VisualizationType = model.VisualizationType.TEXT_ANSWER,
                        fallback: bool = True):
    print(format_text(f"> Answering question: '{question}' AS {visualization}", bold=True))
    chat = ChatOpenAI()
    embeddings = OpenAIEmbeddings()
    answer_chain = CYPHER_QA_PROMPT | chat 

    generator_chain = CYPHER_GENERATION_PROMPT | chat
    driver: neo4j.AsyncDriver = db.connect(request)
    session: neo4j.AsyncSession = driver.session()

    print(format_text("> Entering embedding calculation", bold=True))
    embedding = await embeddings.aembed_query(question)
    print(format_text("> Embedding done", bold=True))

    matches = await find_queries(session, embedding, visualization=visualization) 

    query = None
    if len(matches):
        query = await _generate_query_from_sample(session, chat, question, matches)

    if not query and fallback:
        print(format_text("> No query sample found, generating using default strategy", bold=True))
        query_msg: BaseMessage = await generator_chain.ainvoke({'question': question, 'schema': construct_schema(Neo4jGraph().get_structured_schema, [], [])})
        query = query_msg.content
        query_corrector = QueryCorrector(session, chat=chat)
        query = await query_corrector(query)
        print(format_text(f"> Generated query:", bold=True))
        print(format_text(query, color='yellow'))

    if not query:
        return None
    
    query = query.strip()
    if query.endswith(';'):
        query = query[:-1]
    if 'limit ' not in query.lower():
        query = query + f' LIMIT {result_limit};'
    async with driver.session() as session:
        data = await (await session.run(query)).data()
    if not data:
        return None 
    result = {"queries": [{"query": query, "result": jsonify_result(data, indent=4)}]}
    if visualization == model.VisualizationType.TEXT_ANSWER:
        try:
            answer: BaseMessage = await answer_chain.ainvoke({'question': question, 'context': jsonify_result(data)})
            snippet = answer.content
            result['snippet'] = snippet
        except openai.BadRequestError as e:
            pass
    elif visualization == model.VisualizationType.TABLE:
        result['table'] = {
            'data': data
        }
    elif visualization == model.VisualizationType.BAR_CHART:
        result['barchart'] = {
            'data': data
        }
    return result

async def _search(request: fastapi.Request, question: str) -> model.SearchResult:

    if settings.DEBUG:
        snippet_result = await _answer_question(request, question, visualization=model.VisualizationType.TEXT_ANSWER)
        table_result = await _answer_question(request, question, visualization=model.VisualizationType.TABLE, fallback=False)
        barchart_result = await _answer_question(request, question, visualization=model.VisualizationType.BAR_CHART, fallback=False)
    else:
        answers = await asyncio.gather(
            _answer_question(request, question, visualization=model.VisualizationType.TEXT_ANSWER),
            _answer_question(request, question, visualization=model.VisualizationType.TABLE, fallback=False),
            _answer_question(request, question, visualization=model.VisualizationType.BAR_CHART, fallback=False)
        )
        snippet_result, table_result, barchart_result = answers

    result = {
        'data': [],
        'meta': {}
    }
    if snippet_result and snippet_result['snippet']:
        result['meta']['snippet'] = {
            'snippet': snippet_result['snippet'],
            'queries': snippet_result['queries']
        }
    if table_result and table_result['table']:
        result['meta']['table'] = {
            'columns': list(table_result['table']['data'][0].keys()),
            'data': table_result['table']['data'],
            'queries': table_result['queries'],
        }
    if barchart_result and barchart_result['barchart']:
        cols = list(barchart_result['barchart']['data'][0].keys())
        result['meta']['barchart'] = {
            'x_axis': cols[0],
            'y_axis': cols[1],
            'data': barchart_result['barchart']['data'],
            'queries': barchart_result['queries'],
        }
    return result

# Search
@app.get("/search")
async def search(request: fastapi.Request, question: str) -> model.SearchResult:
    return await _search(request, question)

@app.post("/search")
async def post_search(request: fastapi.Request, payload: model.SearchParam) -> model.SearchResult:
    return await _search(request, payload.question)

@app.get('/config/{identifier}')
async def get_config(request: fastapi.Request, identifier: str):
    async def _job(txn: neo4j.AsyncTransaction):
        query = '''
        MATCH (n:_RAGConfig {name: $name})
        RETURN n
        ''' 
        result = await txn.run(query, parameters={'name': identifier})
        return await result.single()
    session: neo4j.AsyncSession = await db.session(request)
    result: neo4j.Record = await session.execute_read(_job)
    return fastapi.responses.Response(
        content=result['n']['body'],
        media_type=result['n']['filetype'],
        headers={
            'Content-Length': str(result['n']['filesize'])
        }
    )

#@app.get('/config/')
#async def list_configs(request: fastapi.Request) -> model.ItemList[]
#
@app.post('/config/')
async def upload_config(request: fastapi.Request):
    config = await extract_model(model.RAGConfig, request)
    session: neo4j.AsyncSession = await db.session(request)
    embeddings = OpenAIEmbeddings()
    async def _job(txn: neo4j.AsyncTransaction):
        query = '''
        MATCH (n:_RAGConfig {name: $name})
        OPTIONAL MATCH (n)-[]-(q:_RAGQuery)
        OPTIONAL MATCH (q)-[]-(k:_RAGQuestion)
        DETACH DELETE k
        DETACH DELETE q
        DETACH DELETE n
        '''
        result = await txn.run(query, parameters={
            'name': config.metadata.name
        })
        query = '''
        MERGE (n:_RAGConfig {name: $name})
        SET n.filesize = $filesize,
            n.body = $body
        '''
        result = await txn.run(query=query, parameters={
            'name': config.metadata.name,
            'body': config.model_dump_json(),
            'filesize': len(config.model_dump_json()),
            'filetype': 'application/json'
        })
        query = '''
        MATCH (n:_RAGConfig {name: $name})
        MATCH (n)-[]-(q:_RAGQuery)
        DETACH DELETE (q)
        '''
        result = await txn.run(query=query, parameters={
            'name': config.metadata.name,
        })

        for pattern in config.patterns:
            for output in pattern.output:
                query = '''
                    MATCH (n:_RAGConfig {name: $name})
                    MERGE (n)-[:CONTAINS]->(q:_RAGQuery {query: $query, output_type: $output_type})
                '''
                result = await txn.run(query=query, parameters={
                    'name': config.metadata.name,
                    'query': pattern.query,
                    'output_type': output.type
                })
                for question in pattern.questions:
                    query = '''
                        MATCH (n:_RAGConfig {name: $name})-[:CONTAINS]->(q:_RAGQuery {query: $query})
                        MERGE (q)-[:ANSWERS]->(k:_RAGQuestion {question: $question})
                        SET k.embedding = $embedding
                    '''
                    embedding = await embeddings.aembed_query(question.question)
                    result = await txn.run(query=query, parameters={
                        'name': config.metadata.name,
                        'query': pattern.query,
                        'question': question.question,
                        'embedding': embedding
                    })
    result = await session.execute_write(_job)
    return fastapi.responses.RedirectResponse(url=f'/config/{config.metadata.name}')

@app.delete('/config/{identifier}')
async def delete_config(request: fastapi.Request, identifier: str) -> model.Message:
    async def _job(txn: neo4j.AsyncTransaction):
        query = '''
        MATCH (n:_RAGConfig {name: $name})
        OPTIONAL MATCH (n)-[]-(q:_RAGQuery)
        OPTIONAL MATCH (q)-[]-(k:_RAGQuestion)
        DETACH DELETE k
        DETACH DELETE q
        DETACH DELETE n
        '''
        result = await txn.run(query=query, parameters={'name': identifier})
    session: neo4j.AsyncSession = await db.session(request)
    result = await session.execute_write(_job)
    return {
        'msg': f'Deleted {identifier}'
    }

@app.exception_handler(yaml.parser.ParserError)
async def parser_error(exc: yaml.parser.ParserError, request: fastapi.Request, status_code=422) -> model.Message:
    return fastapi.responses.JSONResponse(
        status_code=422,
        content={
            'msg': 'Invalid data type'
        })

# endpoint.RAGPattern.register_views(app)
