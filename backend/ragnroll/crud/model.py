import pydantic
import enum
import typing

N = typing.TypeVar("N", bound=pydantic.BaseModel)

class QueryType(enum.StrEnum):
   CYPHER = 'cypher'

class ItemLinks(pydantic.BaseModel):
    self: pydantic.HttpUrl

class Node(pydantic.BaseModel, typing.Generic[N]):
    id: int
    labels: list[str]
    properties: N

class ScoredNode(Node[N]):
    score: typing.Optional[float] = None

class NodeItem(Node):
    links: ItemLinks

class ItemListMeta(pydantic.BaseModel):
    total_items: typing.Optional[int] = None
    current_page: typing.Optional[int] = None
    page_size: typing.Optional[int] = None
    total_pages: typing.Optional[int] = None

class ItemListLinks(pydantic.BaseModel):
    first_page: typing.Optional[pydantic.AnyHttpUrl] = None
    prev_page: typing.Optional[pydantic.AnyHttpUrl] = None
    next_page: typing.Optional[pydantic.AnyHttpUrl] = None
    final_page: typing.Optional[pydantic.AnyHttpUrl] = None

class ItemList(pydantic.BaseModel, typing.Generic[N]):
    data: list[N]
    meta: ItemListMeta
    links: ItemListLinks

class SearchParam(pydantic.BaseModel):
    question: str

class SearchData(pydantic.BaseModel):
    title: str
    match: str
    url: pydantic.AnyHttpUrl

class SearchMeta(pydantic.BaseModel):
    snippet: typing.Optional[str]
    queries: list[typing.Optional[str]]

class SearchResult(pydantic.BaseModel):
    data: list[SearchData]
    meta: SearchMeta

class Message(pydantic.BaseModel):
    msg: typing.Optional[str]


