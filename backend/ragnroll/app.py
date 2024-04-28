import fastapi
import yaml.parser 
from . import model
from . import db
from . import settings
import neo4j
import neo4j.exceptions
from langchain_openai import OpenAIEmbeddings
from .util import format_text, extract_model
import asyncio
import neo4j.spatial
import neo4j.time
import neo4j.graph
import yaml
import yaml.parser
from .rag import answer_question

app = fastapi.FastAPI(title="RAG'n'Roll")

async def _search(request: fastapi.Request, question: str) -> model.SearchResult:
    print(format_text(f"> Searching: '{question}'", bold=True))
    print(format_text("> Entering embedding calculation", bold=True))
    embeddings = OpenAIEmbeddings()
    embedding = await embeddings.aembed_query(question)
    print(format_text("> Embedding done", bold=True))

    answer_promises = []
    for v in model.VisualizationType:
        opts = dict(
            request=request,
            question=question,
            embedding=embedding,
            visualization=v
        )
        if v == model.VisualizationType.TEXT_ANSWER:
            opts['fallback'] = True 
        answer_promises.append(answer_question(**opts))

    if settings.DEBUG:
        answers = [await p for p in answer_promises]
    else:
        answers = await asyncio.gather(*answer_promises)

    result = {
        'data': [],
        'meta': {}
    }
    result['data'] = [a for a in answers if a]
    return result

# Search
@app.get("/search", response_model_exclude_none=True, response_model_exclude_unset=True)
async def search(request: fastapi.Request, question: str) -> model.SearchResult:
    return await _search(request, question)

@app.post("/search", response_model_exclude_none=True, response_model_exclude_unset=True)
async def post_search(request: fastapi.Request, payload: model.SearchParam) -> model.SearchResult:
    return await _search(request, payload.question)

@app.get('/expertise/{identifier}')
async def get_expertise(request: fastapi.Request, identifier: str):
    async def _job(txn: neo4j.AsyncTransaction):
        query = '''
        MATCH (n:_RAGExpertise {name: $name})
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

@app.post('/expertise/')
async def upload_expertise(request: fastapi.Request):
    config = await extract_model(model.RAGExpertise, request)
    session: neo4j.AsyncSession = await db.session(request)
    embeddings = OpenAIEmbeddings()
    async def _job(txn: neo4j.AsyncTransaction):
        query = '''
        MATCH (n:_RAGExpertise {name: $name})
        OPTIONAL MATCH (n)-[]-(p:_RAGPattern)
        OPTIONAL MATCH (p)-[]-(q:_RAGQuery)
        OPTIONAL MATCH (q)-[]-(k:_RAGQuestion)
        DETACH DELETE k
        DETACH DELETE q
        DETACH DELETE n
        '''
        result = await txn.run(query, parameters={
            'name': config.metadata.name
        })
        query = '''
        MERGE (n:_RAGExpertise {name: $name})
        SET n.filesize = $filesize,
            n.body = $body
        '''
        result = await txn.run(query=query, parameters={
            'name': config.metadata.name,
            'body': config.model_dump_json(),
            'filesize': len(config.model_dump_json()),
            'filetype': 'application/json'
        })

        for pattern in config.spec.patterns:
            for answer in pattern.answers:
                query = '''
                    MATCH (n:_RAGExpertise {name: $name})
                    MERGE (p:_RAGPattern {name: $pattern_name})
                    MERGE (n)-[:CONTAINS]->(p)
                    MERGE (p)-[:CONTAINS]->(q:_RAGQuery {query: $query, visualization: $visualization})
                '''
                result = await txn.run(query=query, parameters={
                    'name': config.metadata.name,
                    'pattern_name': pattern.name,
                    'query': answer.query,
                    'visualization': answer.visualization
                })
            for question in pattern.questions:
                query = '''
                    MATCH (n:_RAGExpertise {name: $name})-[:CONTAINS]->(p:_RAGPattern {name: $pattern_name})
                    MERGE (p)-[:CONTAINS]->(k:_RAGQuestion {question: $question, language: $language})
                    SET k.embedding = $embedding
                '''
                embedding = await embeddings.aembed_query(question.question)
                result = await txn.run(query=query, parameters={
                    'name': config.metadata.name,
                    'pattern_name': pattern.name,
                    'question': question.question,
                    'language': question.language,
                    'embedding': embedding
                })
    result = await session.execute_write(_job)
    return fastapi.responses.RedirectResponse(url=f'/expertise/{config.metadata.name}')

@app.delete('/expertise/{identifier}')
async def delete_expertise(request: fastapi.Request, identifier: str) -> model.Message:
    async def _job(txn: neo4j.AsyncTransaction):
        query = '''
        MATCH (n:_RAGExpertise {name: $name})
        OPTIONAL MATCH (n)-[]-(p:_RAGPattern)
        OPTIONAL MATCH (p)-[]-(q:_RAGQuery)
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
async def parser_error(exc: yaml.parser.ParserError, request: fastapi.Request) -> model.Message:
    return fastapi.responses.JSONResponse(
        status_code=422,
        content={
            'msg': 'Invalid data type'
        })

@app.exception_handler(fastapi.HTTPException)
async def http_exc(exc: fastapi.HTTPException):
    return fastapi.responses.JSONResponse(
        status_code=exc.status_code,
        content={
            'msg': exc.detail
        }
    )

