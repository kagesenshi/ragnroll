from ragnroll import settings
import neo4j
import fastapi
import ssl
import json
import abc
import pydantic
import typing
from . import model

def connect(request: fastapi.Request) -> neo4j.AsyncDriver:
    params = dict(
        uri=settings.NEO4J_ADDRESS,
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

S = typing.TypeVar("S")

class Collection(abc.ABC, typing.Generic[S]):

    def __init__(self, session: neo4j.AsyncSession, label: str, schema: type[pydantic.BaseModel]):
        self.label = label
        self.session = session
        self.schema = schema

    @property
    def create_query(self) -> str:
        fields = []
        for name, field in self.schema.model_fields.items():
            fields.append(f'{name}: ${name}')
        return '''
            CREATE (n:%s {%s})
        ''' % (self.label, ',\n'.join(fields))
    
    @property
    def update_query(self) -> str:
        fields = []
        for name, field in self.schema.model_fields.items():
            fields.append(f'{name}: ${name}')
        return '''
            MATCH (n:%s)
                WHERE id(n) = $__node_id
            SET n = {%s}
            RETURN id(n) as identifier, n, labels(n) as node_labels
        ''' % (self.label, ',\n'.join(fields))

    async def create(self, item: model.RetrievalStrategy):
        session = self.session
        return await session.execute_write(self._create, item)

    async def _create(self, txn: neo4j.AsyncTransaction, item: pydantic.BaseModel):
        res = await txn.run(self.create_query, parameters=item.model_dump())
        return True
    
    async def update(self, node_id: int, item: pydantic.BaseModel) -> model.Node:
        return await self.session.execute_write(self._update, node_id, item)
    
    async def _update(self, txn: neo4j.AsyncTransaction, node_id: int, item: model.RetrievalStrategy) -> model.Node:
        params = item.model_dump()
        params['__node_id'] = node_id
        res = await txn.run(self.update_query, parameters=params)
        record = await res.single()
        return model.Node[self.schema](id=record['identifier'], properties=record['n'], labels=record['node_labels'])
    
    async def list_all(self, limit=100, offset=0) -> list[model.Node]:
        return await self.session.execute_read(self._list_all, limit=limit, offset=offset)
    
    async def _list_all(self, txn: neo4j.AsyncTransaction, limit=100, offset=0) -> list[model.Node[S]]:
        query = '''
        MATCH (n:%s)
        RETURN n, id(n) as identifier, labels(n) as node_labels
            SKIP $offset
            LIMIT $limit
        ''' % self.label
        res = await txn.run(query, parameters={'limit': limit, 'offset': offset})
        return [model.Node[self.schema](id=r['identifier'], properties=r['n'], labels=r['node_labels']) for r in await res.data()]
    
    async def get(self, node_id) -> model.Node:
        return await self.session.execute_read(self._get_by_id, node_id)
    
    async def _get_by_id(self, txn: neo4j.AsyncTransaction, node_id) -> model.Node[S]:
        query = '''
        MATCH (n:%s)
            WHERE id(n) = $__node_id 
            RETURN n, id(n) as identifier, labels(n) as node_labels
        ''' % self.label
        res = await txn.run(query, parameters={'__node_id': node_id})
        r = await res.single()
        if r:
            return model.Node[self.schema](id=r['identifier'], properties=r['n'], labels=r['node_labels'])
        return None


    async def delete(self, node_id: int) -> bool:
        return await self.session.execute_write(self._delete, node_id)
    
    async def _delete(self, txn: neo4j.AsyncTransaction, node_id: int):
        query = '''
        MATCH (n:%s)
            WHERE id(n) = $__node_id 
            DETACH DELETE n
        ''' % self.label
        res = await txn.run(query, parameters={'__node_id': node_id})
        return True 
    
    async def total_count(self) -> int:
        return await self.session.execute_read(self._total_count)
    
    async def _total_count(self, txn: neo4j.AsyncTransaction) -> int:
        query = '''
        MATCH (n:%s)
        RETURN COUNT(n) as total
        ''' % self.label
        res = await txn.run(query, parameters={})
        return (await res.single())['total']

def RetrievalStrategy(session: neo4j.AsyncSession): 

    return Collection(session, 'RetrievalStrategy', model.RetrievalStrategy)