import pydantic
import enum
import typing
from .crud.model import *

class QueryType(enum.StrEnum):
   CYPHER = 'cypher'

class VisualizationType(enum.StrEnum):
    TEXT_ANSWER = 'text-answer'
    BAR_CHART = 'bar-chart'

class RetrievalQuestion(pydantic.BaseModel):
    question: str
    embedding: typing.Optional[list[float]] = None

class RetrievalQuery(pydantic.BaseModel):
    query: str
    query_type: QueryType = 'cypher'
    visualization: VisualizationType = 'text-answer'

class Document(pydantic.BaseModel):
    title: typing.Optional[str]
    description: typing.Optional[str]
    file_name: str
    file_size: int
    file_type: str
    file_checksum: str

