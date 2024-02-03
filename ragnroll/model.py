import pydantic
import enum
import typing
from .crud.model import *

class QueryType(enum.StrEnum):
   CYPHER = 'cypher'

class RetrievalStrategy(pydantic.BaseModel):
    question: str
    query: str
    query_type: QueryType = 'cypher'
    answer_example: str
    embedding: typing.Optional[list[float]] = None

class Document(pydantic.BaseModel):
    title: typing.Optional[str]
    description: typing.Optional[str]
    file_name: str
    file_size: int
    file_type: str
    file_checksum: str

