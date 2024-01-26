import pydantic
import enum
import typing

class QueryType(enum.StrEnum):
   SQL = 'sql'
   CYPHER = 'cypher'

class RetrievalStrategy(pydantic.BaseModel):
    question: str
    query: str
    query_type: QueryType
    answer_example: str

class Document(pydantic.BaseModel):
    title: typing.Optional[str]
    description: typing.Optional[str]
    file_name: str
    file_size: int
    file_type: str
    file_checksum: str

class ItemLinks(pydantic.BaseModel):
    self: pydantic.HttpUrl


N = typing.TypeVar("N")

class Node(pydantic.BaseModel, typing.Generic[N]):
    id: int
    labels: list[str]
    properties: N

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
    query: str

class SearchData(pydantic.BaseModel):
    title: str
    match: str
    url: pydantic.AnyHttpUrl

class SearchMeta(pydantic.BaseModel):
    snippet: str

class SearchResult(pydantic.BaseModel):
    data: list[SearchData]
    meta: SearchMeta

class Message(pydantic.BaseModel):
    msg: typing.Optional[str]


