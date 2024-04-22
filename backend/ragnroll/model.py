import pydantic
import enum
import typing
import neo4j
from .crud.model import *

class QueryType(enum.StrEnum):
   CYPHER = 'cypher'

class VisualizationType(enum.StrEnum):
    TEXT_ANSWER = 'text-answer'
    TABLE = 'table'
    BAR_CHART = 'bar-chart'
    LINE_CHART = 'line-chart'
   
class RAGPatternOutput(pydantic.BaseModel):
    type: VisualizationType

class RAGQuestion(pydantic.BaseModel):
    question: str 

class RAGPattern(pydantic.BaseModel):
    query: str
    output: list[RAGPatternOutput]
    questions: list[RAGQuestion]

class ConfigMetadata(pydantic.BaseModel):
    name: str = pydantic.StringConstraints(strip_whitespace=True, strict=True, pattern=r'^[a-z0-9\-]*$')

class RAGConfig(pydantic.BaseModel):
    metadata: ConfigMetadata
    patterns: list[RAGPattern] 