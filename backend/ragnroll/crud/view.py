from .collection import Collection, NodeCollection
import typing
import neo4j
import fastapi
import urllib.parse
import pydantic
from . import model
from . import db
import abc
import enum

S = typing.TypeVar("S", bound=pydantic.BaseModel) # Model Schema

class NodeCollectionEndpoints(typing.Generic[S]):
    list_endpoint: str 
    create_endpoint: str 
    read_endpoint: str 
    update_endpoint: str 
    delete_endpoint: str

    def __init__(self, name: str, label: str, schema: type[S],
                 before_create: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', S], typing.Awaitable[None]]] = None, 
                 after_create: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', S], typing.Awaitable[None]]] = None,
                 before_update: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', int, S], typing.Awaitable[None]]] = None,
                 after_update: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', int, S], typing.Awaitable[None]]] = None,
                 before_delete: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', int], typing.Awaitable[None]]] = None,
                 after_delete: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, 'NodeCollection[S]', int], typing.Awaitable[None]]] = None,
                 transform_nodes: typing.Optional[typing.Callable[[neo4j.AsyncTransaction, list[model.Node[S]]], typing.Awaitable[list[model.Node[S]]]]] = None
                 ) -> None:
        self.label = label
        self.schema = schema
        self.name = name
        self.list_endpoint = f'list_{name}'
        self.create_endpoint = f'create_{name}'
        self.read_endpoint = f'read_{name}'
        self.update_endpoint = f'update_{name}'
        self.delete_endpoint = f'delete_{name}'
        self.collection_callbacks = {
            'before_create': before_create,
            'after_create': after_create,
            'before_update': before_update,
            'after_update': after_update,
            'before_delete': before_delete,
            'after_delete': after_delete,
            'transform_nodes': transform_nodes
        }

    async def factory(self, request: fastapi.Request) -> NodeCollection:
        session = await db.session(request)
        return NodeCollection(session, self.label, self.schema, **self.collection_callbacks)

    async def view_factory(self, request: fastapi.Request) -> 'NodeCollectionView':
        collection = await self.factory(request)
        return NodeCollectionView[self.schema](request, collection, self)
    
    def register_views(self, app):
        @app.post(f"/{self.name}", name=self.create_endpoint)
        async def create(request: fastapi.Request, payload: self.schema) -> model.NodeItem[self.schema]:
            view = await self.view_factory(request) 
            return await view.create(payload)
        
        @app.get(f"/{self.name}", name=self.list_endpoint, response_model_exclude_none=True)
        async def list_all(request: fastapi.Request, page:int =0, page_size: int=100) -> model.ItemList[model.NodeItem[self.schema]]:
            view = await self.view_factory(request)
            res= await view.list_all(page, page_size)
            return res
        
        @app.get(f"/{self.name}/{{identifier}}", name=self.read_endpoint)
        async def get(request: fastapi.Request, identifier: int) -> model.NodeItem[self.schema]:
            view = await self.view_factory(request)
            return await view.get(identifier)
        
        @app.put(f"/{self.name}/{{identifier}}", name=self.update_endpoint)
        async def update(request: fastapi.Request, identifier: int, payload: self.schema) -> model.NodeItem[self.schema]:
            view = await self.view_factory(request)
            return await view.update(identifier, payload)
        
        @app.delete(f"/{self.name}/{{identifier}}", name=self.delete_endpoint)
        async def delete(request: fastapi.Request, identifier: int) -> model.Message:
            view = await self.view_factory(request)
            return await view.delete(identifier)

class NodeCollectionView(typing.Generic[S]):

    def __init__(self, request: fastapi.Request, collection: NodeCollection[S],
                 endpoints: NodeCollectionEndpoints):
        self.col = collection
        self.request = request
        self.create_endpoint = endpoints.create_endpoint
        self.list_endpoint = endpoints.list_endpoint
        self.read_endpoint = endpoints.read_endpoint
        self.update_endpoint = endpoints.update_endpoint
        self.delete_endpoint = endpoints.delete_endpoint

    async def create(self, payload: S) -> model.NodeItem[S]:
        record = await self.col.create(payload)
        data = record.model_dump()
        data['links'] = model.ItemLinks(self=pydantic.HttpUrl(str(self.request.url_for(self.read_endpoint, 
                                                                      identifier=record.id))))
        return model.NodeItem[self.col.schema](**data)
    
    async def get(self, identifier: int) -> model.NodeItem[S]:
        record = await self.col.get(identifier)
        if not record:
            raise fastapi.HTTPException(404)
        data = record.model_dump()
        data['links'] = model.ItemLinks(self=pydantic.HttpUrl(str(self.request.url_for(self.read_endpoint, 
                                                                      identifier=record.id))))
        return model.NodeItem[self.col.schema](**data)

    async def list_all(self, page:int = 0, page_size: int = 100) -> model.ItemList[model.NodeItem[S]]:
        collection = self.col
        total_count = await collection.total_count()
        items = await collection.list_all(limit=page_size, offset=page * page_size)
        total_pages = int(total_count / page_size)
        if page > total_pages:
            raise fastapi.HTTPException(404)
        pagemeta = model.ItemListMeta(page_size=page_size, current_page=page, total_items=total_count, total_pages=total_pages)
        links = model.ItemListLinks()
        here_url = self.request.url_for(self.list_endpoint)
        links.first_page = pydantic.HttpUrl('%s?%s' % (here_url, urllib.parse.urlencode({'page': 0, 'page_size': page_size})))
        if total_pages != 0:
            links.final_page = pydantic.HttpUrl('%s?%s' % (here_url, urllib.parse.urlencode({'page': total_pages, 'page_size': page_size})))
        if page > 0:
            links.prev_page = pydantic.HttpUrl('%s?%s' % (here_url, urllib.parse.urlencode({'page': page-1, 'page_size': page_size})))
        if page < total_pages:
            links.next_page = pydantic.HttpUrl('%s?%s' % (here_url, urllib.parse.urlencode({'page': page+1, 'page_size': page_size})))
        result = model.ItemList[model.NodeItem[self.col.schema]](**{
            'data': [
                dict(
                    links={'self': pydantic.HttpUrl(str(self.request.url_for(self.read_endpoint, identifier=item.id)))}, 
                                  **item.model_dump())
                for item in items],
            'meta': pagemeta,
            'links': links
        })
        return result

    async def update(self, identifier: int, payload: S) -> model.NodeItem[S]:
        collection = self.col
        record = await collection.get(identifier)
        if not record:
            raise fastapi.HTTPException(404)
        updated = await collection.update(identifier, payload)
        data = updated.model_dump()
        data['links'] = model.ItemLinks(
            self=str(self.request.url_for(self.read_endpoint, 
                    identifier=updated.id)))
        return model.NodeItem[self.col.schema](**data)

    async def delete(self, identifier: int) -> model.Message:
        record = await self.col.get(identifier)
        if not record:
            raise fastapi.HTTPException(404)
        await self.col.delete(identifier)
        return model.Message(msg='success')
    