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
                        embedding: list[float]) -> list[QuerySample]:
    async def _job(txn: neo4j.AsyncTransaction):
        count = 5
        min_score = 0.9
        cypher = '''
            CALL db.index.vector.queryNodes('ragquestion_embedding', $count, $embedding)
            YIELD node, score
            WITH node, score
               WHERE '_RAGQuestion' in labels(node)
               AND score > $min_score
            MATCH (query:_RAGQuery)-[:CONTAINS]-(p:_RAGPattern)-[:CONTAINS]-(node)
            RETURN distinct query, node as question, score
           ''' 
        res = await txn.run(cypher, parameters={'embedding': embedding, 'count': count, 
                                                'min_score': min_score})
        queries = await res.data()
        return queries
    
    matches = await session.execute_read(_job)
    matches = [QuerySample(question=m['question']['question'], 
                query=m['query']['query'],
                visualization=m['query']['visualization'],
                score=m['score']) for m in matches]
    return matches

async def generate_query_from_sample(session: neo4j.AsyncSession, chat: ChatOpenAI, question: str, 
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

async def answer_question(request: fastapi.Request, question: str, 
                           embedding: typing.Optional[list[float]] = None, result_limit: int = 50,
                        visualization: model.VisualizationType = model.VisualizationType.TEXT_ANSWER,
                        fallback: bool = False):
    
    print(format_text(f"> Answering question: '{question}' AS {visualization}", bold=True))
    chat = ChatOpenAI()

    answer_chain = CYPHER_QA_PROMPT | chat 

    generator_chain = CYPHER_GENERATION_PROMPT | chat
    driver: neo4j.AsyncDriver = db.connect(request)
    session: neo4j.AsyncSession = driver.session()

    if embedding is None:
        print(format_text("> Entering embedding calculation", bold=True))
        embeddings = OpenAIEmbeddings()
        embedding = await embeddings.aembed_query(question)
        print(format_text("> Embedding done", bold=True))

    queries = await find_queries(session, embedding)
    matches = [m for m in queries if m.visualization == visualization]
    other_matches = [m for m in queries if m.visualization != visualization]
    if not matches and fallback and other_matches:
        # do not fallback if there's matches in other types
        return None
    
    query = None
    if matches:
        query = await generate_query_from_sample(session, chat, question, matches)

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
    result = {"queries": [{"query": query, "result": jsonify_result(data, indent=4)}],
              'visualization': visualization}
    if visualization == model.VisualizationType.TEXT_ANSWER:
        try:
            answer: BaseMessage = await answer_chain.ainvoke({'question': question, 'context': jsonify_result(data)})
            snippet = answer.content
            result['data'] = [{'answer': snippet}]
            result['fields'] = ['answer']
        except openai.BadRequestError as e:
            pass
    elif visualization == model.VisualizationType.TABLE:
        result['data'] = data
        result['fields'] = list(data[0].keys())
    elif visualization == model.VisualizationType.BAR_CHART:
        cols = list(data[0].keys())
        result['data'] = data
        result['fields'] = cols
        result['axes'] = {'x': cols[0], 'y': cols[1]}
    return result

