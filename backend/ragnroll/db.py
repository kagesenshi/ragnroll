from ragnroll import settings
import neo4j
import fastapi
import ssl
import json
import abc
import pydantic
import typing
from . import model
from .crud.collection import Collection
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
import asyncio

def connect(request: fastapi.Request) -> neo4j.AsyncDriver:
    params = dict(
        uri=settings.NEO4J_URI,
        database=settings.NEO4J_DATABASE,
    )

    if settings.NEO4J_USE_SSL:
        params['encrypted'] = True
        if settings.NEO4J_SSL_CA_CERT:
            params['trusted_certificates'] = neo4j.TrustCustomCAs(settings.NEO4J_SSL_CA_CERT)

    auth_header = request.headers.get('Authorization', default=None)
    if settings.NEO4J_USE_BEARER_TOKEN and auth_header and auth_header.lower().startswith('bearer'):
        params['auth'] = neo4j.bearer_auth(auth_header.split(' ')[1])
    else:
        if settings.NEO4J_USERNAME and settings.NEO4J_PASSWORD:
            params['auth'] = (settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        else:
            raise fastapi.HTTPException(status_code=401, detail='Neither database login configured nor authorization header provided')

    return neo4j.AsyncGraphDatabase.driver(**params)

async def session(request: fastapi.Request) -> neo4j.AsyncSession:
    driver: neo4j.AsyncDriver = connect(request)
    return driver.session()

class RetrievalQuestion(Collection[model.RetrievalQuestion]):
    
    def __init__(self, session: neo4j.AsyncSession, chat: BaseChatModel, embeddings: Embeddings): 
        self.chat = chat
        self.embeddings = embeddings
        return super().__init__(session, 'RetrievalQuestion', model.RetrievalQuestion)
    
    async def match_question(self, query: str, count: int = 10, min_score=0) -> list[model.ScoredNode[model.RetrievalQuestion]]:
        await self.session.execute_write(self._create_vector_index)
        return await self.session.execute_read(self._match_question, query, count = count, min_score = min_score)
    
    async def create(self, item: model.RetrievalQuestion):
        item.embedding = await self.embeddings.aembed_query(item.question)
        return await super().create(item)
    
    async def update(self, node_id: int, item: model.RetrievalQuestion) -> model.Node[model.RetrievalQuestion]:
        item.embedding = await self.embeddings.aembed_query(item.question)
        return await super().update(node_id, item)

    async def _create_vector_index(self, txn: neo4j.AsyncTransaction):
        cypher = '''
        CREATE VECTOR INDEX questions_embedding IF NOT EXISTS
            FOR (n:%s)
            ON (n.embedding)
            OPTIONS { indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
                }
            }
        ''' % (self.label)
        res = await txn.run(cypher, parameters={})
        return None
    
    async def _match_question(self, txn: neo4j.AsyncTransaction, query: str, count: int =10, min_score: int=0) -> model.ScoredNode[model.RetrievalQuestion]:
        embedding = await self.embeddings.aembed_query(query)
        cypher = '''
        CALL db.index.vector.queryNodes('questions_embedding', $count, $embedding)
        YIELD node, score
        WITH node, score
            WHERE $label in labels(node)
            AND score > $min_score
        RETURN id(node) as identifier, node, labels(node) as node_labels, score
        ''' 
        res = await txn.run(cypher, parameters={'label': self.label, 'embedding': embedding, 'count': count, 'min_score': min_score})
        return [model.ScoredNode[self.schema](id=r['identifier'], properties=r['node'], labels=r['node_labels'], score=r['score']) for r in await res.data()]
