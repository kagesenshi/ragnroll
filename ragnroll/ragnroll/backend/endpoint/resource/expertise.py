from ... import db, model
from ...router import router as app

import fastapi
import neo4j

from ...langchain import embeddings_model


@app.get('/resource/expertise/v1', response_model_exclude_none=True, response_model_exclude_unset=True)
async def list_expertise(request: fastapi.Request) -> model.Result[list[model.ConfigMetadata]]:
    async def _job(txn: neo4j.AsyncTransaction):
        query = '''
        MATCH (n:_RAGExpertise)
        RETURN n.name as name
        '''
        result = await txn.run(query)
        return await result.data()
    session: neo4j.AsyncSession = await db.session(request)
    results = await session.execute_read(_job)
    return model.Result[list[model.ConfigMetadata]](data=results)


@app.get('/resource/expertise/v1/{identifier}')
async def get_expertise(request: fastapi.Request, identifier: str) -> model.RAGExpertise:
    async def _job(txn: neo4j.AsyncTransaction):
        query = '''
        MATCH (n:_RAGExpertise {name: $name})
        RETURN n
        '''
        result = await txn.run(query, parameters={'name': identifier})
        return await result.single()
    session: neo4j.AsyncSession = await db.session(request)
    result: neo4j.Record = await session.execute_read(_job)
    return model.RAGExpertise.model_validate_json(result['n']['body'])


@app.post('/resource/expertise/v1', response_class=fastapi.responses.RedirectResponse, status_code=303)
async def upload_expertise(request: fastapi.Request, config: model.RAGExpertise):
    session: neo4j.AsyncSession = await db.session(request)
    async def _job(txn: neo4j.AsyncTransaction):
        query = '''
        MATCH (n:_RAGExpertise {name: $name})
        OPTIONAL MATCH (n)-[]-(p:_RAGPattern)
        OPTIONAL MATCH (p)-[]-(o:_RAGOutput)
        OPTIONAL MATCH (o)-[]-(q:_RAGQuery)
        OPTIONAL MATCH (p)-[]-(k:_RAGQuestion)
        DETACH DELETE o
        DETACH DELETE k
        DETACH DELETE q
        DETACH DELETE n
        DETACH DELETE p
        '''
        result = await txn.run(query, parameters={
            'name': config.metadata.name
        })
        query = '''
        MERGE (n:_RAGExpertise {name: $name})
        SET n.filesize = $filesize,
            n.body = $body
        '''
        jsondata = config.model_dump_json(indent=4)
        result = await txn.run(query=query, parameters={
            'name': config.metadata.name,
            'body': jsondata,
            'filesize': len(jsondata),
            'filetype': 'application/json'
        })

        for pattern in config.spec.patterns:
            query = '''
                MERGE (n:_RAGExpertise {name: $expertise_name})
                MERGE (p:_RAGPattern {expertise: $expertise_name, name: $pattern_name})
                MERGE (n)-[:HAS_PATTERN]-(p)
            '''
            await txn.run(query=query, parameters={
                'expertise_name': config.metadata.name,
                'pattern_name': pattern.name,
            })
            for question in pattern.questions:
                query = '''
                    MATCH (p:_RAGPattern {expertise: $expertise_name, name: $pattern_name})
                    MERGE (p)-[:HAS_QUESTION]->(k:_RAGQuestion {expertise: $expertise_name, pattern: $pattern_name, name: $question_name, question: $question, language: $language})
                    SET k.embedding = $embedding
                '''
                embedding = await embeddings_model.aembed_query(question.question)
                await txn.run(query=query, parameters={
                    'expertise_name': config.metadata.name,
                    'pattern_name': pattern.name,
                    'question_name': question.name,
                    'question': question.question,
                    'language': question.language,
                    'embedding': embedding
                })
            for output in pattern.outputs:
                for sample in output.samples:
                    query = '''
                        MATCH (p:_RAGPattern {expertise: $expertise_name, name: $pattern_name})
                        MERGE (o:_RAGOutput {expertise: $expertise_name, pattern: $pattern_name, name: $output_name})
                        MERGE (o)-[:HAS_QUERY]->(q:_RAGQuery {expertise: $expertise_name, pattern: $pattern_name, output: $output_name, query: $query})
                        MERGE (p)-[:HAS_OUTPUT]->(o)
                        SET o.visualization = $visualization
                        SET o.order = $order
                    '''
                    await txn.run(query=query, parameters={
                        'expertise_name': config.metadata.name,
                        'pattern_name': pattern.name,
                        'output_name': output.name,
                        'query': sample.query,
                        'visualization': output.visualization,
                        'order': output.order
                    })
                    for question in sample.questions:
                        query = '''
                            MATCH (question:_RAGQuestion {expertise: $expertise_name, pattern: $pattern_name, name: $question_name})
                            MATCH (query:_RAGQuery {expertise: $expertise_name, pattern: $pattern_name, output: $output_name, query: $query})
                            MERGE (query)-[:ANSWERS]->(question)
                        '''
                        await txn.run(query=query, parameters={
                            'expertise_name': config.metadata.name,
                            'pattern_name': pattern.name,
                            'question_name': question.name,
                            'output_name': output.name,
                            'query': sample.query
                        })
    result = await session.execute_write(_job)
    return fastapi.responses.RedirectResponse(url=f'/expertise/{config.metadata.name}', status_code=303)


@app.delete('/resource/expertise/v1/{identifier}', response_model_exclude_unset=True)
async def delete_expertise(request: fastapi.Request, identifier: str) -> model.Result[model.Message]:
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
        await txn.run(query=query, parameters={'name': identifier})
    session: neo4j.AsyncSession = await db.session(request)
    await session.execute_write(_job)
    return model.Result[model.Message](
        data=model.Message(message=f'Deleted {identifier}')
    )