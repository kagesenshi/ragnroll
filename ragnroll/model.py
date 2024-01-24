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

class Node(pydantic.BaseModel):
    id: int
    labels: list[str]
    properties: dict[str, typing.Any]
    