import typing
import pydantic
import neo4j
import abc 
from . import model

S = typing.TypeVar("S", bound=pydantic.BaseModel)
T = typing.TypeVar("T", bound=pydantic.BaseModel)
R = typing.TypeVar("R", bound=pydantic.BaseModel)

class Collection(abc.ABC, typing.Generic[T]):

    def __init__(self, session: neo4j.AsyncSession, label: str, schema: type[T]):
        self.label = label
        self.schema = schema
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

    def __init__(self, session: neo4j.AsyncSession, label: str, schema: type[S],
                 before_create: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', S], typing.Awaitable[None]]] = None, 
                 after_create: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', int, S], typing.Awaitable[None]]] = None,
                 before_update: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', int, S], typing.Awaitable[None]]] = None,
                 after_update: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', int, S], typing.Awaitable[None]]] = None,
                 before_delete: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', int], typing.Awaitable[None]]] = None,
                 after_delete: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', int], typing.Awaitable[None]]] = None,
                 transform_nodes: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, list[model.Node[S]]], typing.Awaitable[list[model.Node[S]]]]] = None
                 ):
        self.callbacks = {
            'before_create': before_create,
            'after_create': after_create,
            'before_update': before_update,
            'after_update': after_update,
            'before_delete': before_delete,
            'after_delete': after_delete,
            'transform_nodes': transform_nodes
        }
        super().__init__(session, label, schema)

    @property
    def create_query(self) -> str:
        fields = []
        for name, field in self.schema.model_fields.items():
            fields.append(f'{name}: ${name}')
        return '''
            CREATE (n:%s {%s})
            RETURN id(n) as identifier, n, labels(n) as node_labels
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
    
    @property
    def listing_query(self) -> str:
        query = '''
            MATCH (n:%s)
            RETURN n, id(n) as identifier, labels(n) as node_labels
                SKIP $offset
                LIMIT $limit
            ''' % self.label
        return query
    
    @property
    def get_query(self) -> str:
        query = '''
            MATCH (n:%s)
                WHERE id(n) = $__node_id 
                RETURN n, id(n) as identifier, labels(n) as node_labels
            ''' % self.label
        return query
    
    @property
    def delete_query(self) -> str:
        query = '''
            MATCH (n:%s)
                WHERE id(n) = $__node_id 
                DETACH DELETE n
            ''' % self.label
        return query

    @property
    def count_query(self) -> str:    
        query = '''
            MATCH (n:%s)
            RETURN COUNT(n) as total
            ''' % self.label
        return query

    async def create(self, item: S) -> model.Node[S]:
        async def _job(txn: neo4j.AsyncTransaction):
            if self.callbacks['before_create']:
                await self.callbacks['before_create'](txn, self, item)
            res = await txn.run(self.create_query, parameters=item.model_dump())
            record = await res.single()
            if self.callbacks['after_create']:
                node_id = record['identifier']
                await self.callbacks['after_create'](txn, self, node_id, item)
            return model.Node[self.schema](id=record['identifier'], properties=record['n'], labels=record['node_labels'])
        return await self.session.execute_write(_job)
    
    async def update(self, node_id: int, item: S) -> model.Node[S]:
        async def _job(txn: neo4j.AsyncTransaction):
            params = item.model_dump()
            params['__node_id'] = node_id
            if self.callbacks['before_update']:
                await self.callbacks['before_update'](txn, self, node_id, item)
            res = await txn.run(self.update_query, parameters=params)
            if self.callbacks['after_update']:
                await self.callbacks['after_update'](txn, self, node_id, item)
            record = await res.single()
            node = model.Node[self.schema](id=record['identifier'], properties=record['n'], labels=record['node_labels'])
            if self.callbacks['transform_nodes']:
                return self.callbacks['transform_nodes'](txn, [node])[0]
            return node
        return await self.session.execute_write(_job)
    
    async def list_all(self, limit=100, offset=0) -> list[model.Node[S]]:
        async def _job(txn: neo4j.AsyncTransaction):
            res = await txn.run(self.listing_query, parameters={'limit': limit, 'offset': offset})
            nodes = [model.Node[self.schema](id=r['identifier'], properties=r['n'], labels=r['node_labels']) for r in await res.data()]
            if self.callbacks['transform_nodes']:
                return self.callbacks['transform_nodes'](txn, nodes)
            return nodes
        return await self.session.execute_read(_job)
    
    async def get(self, node_id) -> model.Node[S]:
        async def _job(txn: neo4j.AsyncTransaction):
            res = await txn.run(self.get_query, parameters={'__node_id': node_id})
            r = await res.single()
            if r:
                node = model.Node[self.schema](id=r['identifier'], properties=r['n'], labels=r['node_labels'])
                if self.callbacks['transform_nodes']:
                    return self.callbacks['transform_nodes'](txn, [node])[0]
                return node
            return None
        return await self.session.execute_read(_job)

    async def delete(self, node_id: int) -> bool:
        async def _job(txn: neo4j.AsyncTransaction):
            res = await txn.run(self.delete_query, parameters={'__node_id': node_id})
            return True 
        return await self.session.execute_write(_job)
    
    async def total_count(self) -> int:
        async def _job(txn: neo4j.AsyncTransaction):
            res = await txn.run(self.count_query, parameters={})
            return (await res.single())['total']
        return await self.session.execute_read(_job)


class SubCollection(NodeCollection[S], typing.Generic[S, T]):

    def __init__(self, session: neo4j.AsyncSession, label: str, schema: type[S],
                 parent_collection: NodeCollection[T],
                 parent_node_id: int, 
                 relationship: str):
        self.label = label
        self.schema = schema
        self.parent_collection = parent_collection
        self.parent_node_id = parent_node_id
        self.relationship = relationship
        self.session = session

    async def create(self, item: T, rel: typing.Optional[R] = None) -> bool:
        raise NotImplementedError
    
    async def update(self, node_id: int, item: T, rel: typing.Optional[R] = None) -> T:
        raise NotImplementedError
    
    async def list_all(self, limit=100, offset=0) -> list[T]:
        raise NotImplementedError
    
    async def get(self, node_id) -> T:
        raise NotImplementedError
    
    async def delete(self, node_id: int) -> bool:
        raise NotImplementedError
    
    async def total_count(self) -> int:
        raise NotImplementedError
 

class SubNodeCollection(NodeCollection[S], typing.Generic[S, T]):

    def __init__(self, session: neo4j.AsyncSession, label: str, schema: type[S],
                 parent_collection: NodeCollection[T],
                 parent_node_id: int, 
                 relationship: str, 
                 *args, **kwargs):
        self.parent_collection = parent_collection
        self.parent_node_id = parent_node_id
        self.relationship = relationship
        super().__init__(session, label, schema, *args, **kwargs)

    @property
    def create_query(self) -> str:
        fields = []
        for name, field in self.schema.model_fields.items():
            fields.append(f'{name}: ${name}')

        return '''
            MATCH (p:%(parent_label)s) WHERE id(p) = $__parent_node_id
            CREATE (n:%(label)s {%(data)s})
            MERGE (p)-[r:%(relationship)s]-(n)
            RETURN id(n) as identifier, n, labels(n) as node_labels
        ''' % {
            'label': self.label, 
            'data': ',\n'.join(fields),
            'parent_label': self.parent_collection.label,
            'relationship': self.relationship,
        }
    
    async def create(self, item: S) -> model.Node[S]:
        async def _job(txn: neo4j.AsyncTransaction):
            if self.callbacks['before_create']:
                await self.callbacks['before_create'](txn, self, item)
            params = item.model_dump()
            params['__parent_node_id'] = self.parent_node_id
            res = await txn.run(self.create_query, parameters=params)
            record = await res.single()
            if self.callbacks['after_create']:
                node_id = record['identifier']
                await self.callbacks['after_create'](txn, self, node_id, item)
            return model.Node[self.schema](id=record['identifier'], properties=record['n'], labels=record['node_labels'])
        return await self.session.execute_write(_job)
    
