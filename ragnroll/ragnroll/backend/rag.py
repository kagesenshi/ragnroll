import fastapi
import pydantic
import yaml.parser 
from . import model
from . import db
from . import settings
from .langchain import chat_model, embeddings_model
import neo4j
import neo4j.exceptions
import typing
import urllib.parse
from . import prompt
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages.base import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import GraphCypherQAChain
from langchain_community.chains.graph_qa.prompts import CYPHER_GENERATION_PROMPT, CYPHER_QA_PROMPT
from langchain_community.chains.graph_qa.cypher import construct_schema
from langchain_core.runnables.base import RunnableSerializable
from langchain_community.chains.graph_qa.cypher import extract_cypher
from .util import cprint
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
import re

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

    def __init__(self, session: neo4j.AsyncSession, retries=3) -> None:
        self.chain = prompt.cypher_corrector | chat_model
        self.session = session
        self.retries = retries

    async def __call__(self, query: str):
        retry = 0
        while retry < self.retries:
            try:
                async def run(txn: neo4j.AsyncTransaction):
                    return await (await txn.run(f'EXPLAIN {query}')).data()
                res = await self.session.execute_read(run)
                return query
            except (neo4j.exceptions.CypherSyntaxError) as e:
                cprint("> Correcting query: ", bold=True)
                cprint(query, color='yellow')
                cprint(e.message, color='red')
                message: BaseMessage = await self.chain.ainvoke({'query': query, 'error': e.message})
                query = extract_cypher(message.content)
            retry += 1
        return None


class OutputQuery(pydantic.BaseModel):
    question: str 
    query: str
    score: float

class SearchOutput(pydantic.BaseModel):
    visualization: model.VisualizationType
    queries: list[OutputQuery]
    order: int = 0

async def find_queries(session: neo4j.AsyncSession,
                        embedding: list[float]) -> list[SearchOutput]:
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
            MATCH (query)-[HAS_OUTPUT]-(output:_RAGOutput)
            RETURN distinct query, node as question, output, score
           ''' 
        res = await txn.run(cypher, parameters={'embedding': embedding, 'count': count, 
                                                'min_score': min_score})
        queries = await res.data()
        return queries
    
    matches = await session.execute_read(_job)
    outputs = {}
    for m in matches:
        output_name = m['output']['name']
        default_item = dict(
            name=output_name,
            queries=[],
            visualization=m['output']['visualization'],
            order=m['output']['order']
        )
        outputs.setdefault(output_name, default_item)
        outputs[output_name]['queries'].append(
            OutputQuery(
                question=m['question']['question'],
                query=m['query']['query'],
                score=m['score']
            )
        )

    return sorted([SearchOutput(**o) for o in outputs.values()], key=lambda o: o.order)

async def enforce_limit(query: str, result_limit: int = 20):
    limit_chain = prompt.limit_replacer | chat_model
    query = query.strip()
    if query.endswith(';'):
        query = query[:-1]
    if 'limit ' not in query.lower():
        query = query + f' LIMIT {result_limit};'
    limits = re.findall(r'limit *(\d+)', query.lower())
    if limits:
        limit = 0
        try:
            limit = int(limits[-1])
        except ValueError: 
            pass
        if limit > result_limit:
            cprint(f"> Limit exceeds {result_limit}. Replacing limit", bold=True)
            message: BaseMessage = await limit_chain.ainvoke({'result_limit': result_limit, 'query': query})
            query = message.content
    return query

async def generate_query_from_sample(session: neo4j.AsyncSession, question: str, 
                                      samples: list[OutputQuery], result_limit: int = 20):
    cprint("> Entering intent based query generator", bold=True)
    cprint("> Sample queries:", bold=True)
    for s in samples:
        cprint('> ' + s.query, color='yellow')
    chain = prompt.rag_query_generator | chat_model
    message: BaseMessage = await chain.ainvoke({'data': '\n\n'.join([
            f"Question: {sample.question}\nQuery: {sample.query}" for sample in samples
        ]), 'question': question, 'result_limit': result_limit})
    query = message.content
    if query != 'IDONOTKNOW':
        query = await enforce_limit(query, result_limit=result_limit)
        query_corrector = QueryCorrector(session)
        query = await query_corrector(query)
    else:
        return None
    cprint(f"> Generated query:", bold=True)
    cprint(query, color='yellow')
    return query

async def fetch_output(output: SearchOutput, question: str, driver: neo4j.AsyncDriver, result_limit: int = 20):
    answer_chain = CYPHER_QA_PROMPT | chat_model
    async with driver.session() as session:
        query = await generate_query_from_sample(session, question, output.queries, result_limit=result_limit)
    if not query:
        return None
    
    async with driver.session() as session:
        async def run(txn: neo4j.AsyncTransaction):
            return await (await txn.run(query)).data()
        data = await session.execute_read(run)
    if not data:
        return None 
    visualization = output.visualization
    result = {"queries": [{"query": query, "result": jsonify_result(data, indent=4)}],
              'visualization': visualization, 'order': output.order}
    if visualization == model.VisualizationType.TEXT_ANSWER:
        answer: BaseMessage = await answer_chain.ainvoke({'question': question, 'context': jsonify_result(data)})
        snippet = answer.content
        result['data'] = [{'answer': snippet}]
        result['fields'] = ['answer']
    elif visualization == model.VisualizationType.TABLE:
        result['data'] = data
        result['fields'] = list(data[0].keys())
    elif visualization in [model.VisualizationType.BAR_CHART, model.VisualizationType.PIE_CHART, model.VisualizationType.LINE_CHART]:
        cols = list(data[0].keys())
        if len(cols) < 2:
            return None
        result['data'] = data
        result['fields'] = cols
        result['axes'] = {'x': cols[0], 'y': cols[1]}
    result['data'] = result['data'] or []
    return model.SearchResultItem(**result)
   
async def answer_question(question: str, 
                           driver: neo4j.AsyncDriver,
                           embedding: typing.Optional[list[float]] = None, result_limit: int = 20,
                           ) -> list[model.SearchResultItem]:
    
    cprint(f"> Answering question: '{question}'", bold=True)
    if embedding is None:
        cprint("> Entering embedding calculation", bold=True)
        embedding = await embeddings_model.aembed_query(question)
        cprint("> Embedding done", bold=True)

    async with driver.session() as session:
        outputs = await find_queries(session, embedding)

    result_promises = [fetch_output(o, question, driver, result_limit=result_limit) for o in outputs]

    if settings.DEBUG:
        result: list[model.SearchResultItem] = [await p for p in result_promises]
    else:
        result: list[model.SearchResultItem] = await asyncio.gather(*result_promises)

    if not result:
        cprint("> No results found", bold=True, color="red")
    else:
        cprint("Found %s results" % len(result), bold=True, color="green")
    return sorted([r for r in result if r], key=lambda r: r.order)

async def default_search(question: str, driver: neo4j.AsyncDriver, result_limit:int = 20) -> list[model.SearchResultItem]:
    generator_chain = CYPHER_GENERATION_PROMPT | chat_model
    cprint(f"> Generating answer to '{question}' using default strategy", bold=True)
    query_msg: BaseMessage = await generator_chain.ainvoke({'question': question, 'schema': construct_schema(Neo4jGraph().get_structured_schema, [], [])})
    query = query_msg.content
    query = await enforce_limit(query, result_limit=result_limit)
    async with driver.session() as session:
        query_corrector = QueryCorrector(session)
        query = await query_corrector(query)
    cprint(f"> Generated query:", bold=True)
    cprint(query, color='yellow')
    if not query:
        return []
    async with driver.session() as session:
        async def run(txn: neo4j.AsyncTransaction):
            return await (await txn.run(query)).data()
        data = await session.execute_read(run)
    if not data:
        return []
    answer_chain = CYPHER_QA_PROMPT | chat_model
    answer: BaseMessage = await answer_chain.ainvoke({'question': question, 'context': jsonify_result(data)})
    snippet = answer.content
    return [
        model.SearchResultItem(
            data=[{'answer': snippet}], 
            queries=[model.SearchQueryMeta(query=query, result=jsonify_result(data))], 
            visualization=model.VisualizationType.TEXT_ANSWER,
            fields=['answer'])
    ]