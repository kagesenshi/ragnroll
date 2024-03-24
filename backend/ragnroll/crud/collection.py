import typing
import pydantic
import neo4j
import abc 
from . import model

S = typing.TypeVar("S", bound=pydantic.BaseModel)
T = typing.TypeVar("T", bound=pydantic.BaseModel)

class Collection(abc.ABC, typing.Generic[T]):

    def __init__(self, session: neo4j.AsyncSession):
        self.session = session

    async def create(self, item: T) -> bool:
        raise NotImplementedError
    
    async def update(self, node_id: int, item: T) -> T:
        raise NotImplementedError
    
    async def list_all(self, limit=100, offset=0) -> list[T]:
        raise NotImplementedError
    
    async def get(self, node_id) -> T:
        raise NotImplementedError
    
    async def delete(self, node_id: int) -> bool:
        raise NotImplementedError
    
    async def total_count(self) -> int:
        raise NotImplementedError
    
class NodeCollection(Collection[S]):

    def __init__(self, session: neo4j.AsyncSession, label: str, schema: type[S]):
        self.label = label
        self.schema = schema
        super().__init__(session)

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

    async def create(self, item: S) -> bool:
        async def _job(txn: neo4j.AsyncTransaction):
            res = await txn.run(self.create_query, parameters=item.model_dump())
            return True
        return await self.session.execute_write(_job)
    
    async def update(self, node_id: int, item: S) -> model.Node[S]:
        async def _job(txn: neo4j.AsyncTransaction):
            params = item.model_dump()
            params['__node_id'] = node_id
            res = await txn.run(self.update_query, parameters=params)
            record = await res.single()
            return model.Node[self.schema](id=record['identifier'], properties=record['n'], labels=record['node_labels'])           
        return await self.session.execute_write(_job)
    
    async def list_all(self, limit=100, offset=0) -> list[model.Node[S]]:
        async def _job(txn: neo4j.AsyncTransaction):
            query = '''
            MATCH (n:%s)
            RETURN n, id(n) as identifier, labels(n) as node_labels
                SKIP $offset
                LIMIT $limit
            ''' % self.label
            res = await txn.run(query, parameters={'limit': limit, 'offset': offset})
            return [model.Node[self.schema](id=r['identifier'], properties=r['n'], labels=r['node_labels']) for r in await res.data()]
        return await self.session.execute_read(_job)
    
    async def get(self, node_id) -> model.Node[S]:
        async def _job(txn: neo4j.AsyncTransaction):
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
        return await self.session.execute_read(_job)

    async def delete(self, node_id: int) -> bool:
        async def _job(txn: neo4j.AsyncTransaction):
            query = '''
            MATCH (n:%s)
                WHERE id(n) = $__node_id 
                DETACH DELETE n
            ''' % self.label
            res = await txn.run(query, parameters={'__node_id': node_id})
            return True 
        return await self.session.execute_write(_job)
    
    async def total_count(self) -> int:
        async def _job(txn: neo4j.AsyncTransaction):
            query = '''
            MATCH (n:%s)
            RETURN COUNT(n) as total
            ''' % self.label
            res = await txn.run(query, parameters={})
            return (await res.single())['total']
        return await self.session.execute_read(_job)