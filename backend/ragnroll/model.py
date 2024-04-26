import pydantic
import enum
import typing
import neo4j


class SearchParam(pydantic.BaseModel):
    question: str

class SearchData(pydantic.BaseModel):
    title: str
    match: str
    url: pydantic.AnyHttpUrl

class SearchQueryMeta(pydantic.BaseModel):

    query: str
    result: str

class SnippetResult(pydantic.BaseModel):
    snippet: str
    queries: list[SearchQueryMeta]   

class TableResult(pydantic.BaseModel):
    columns: list[str]
    data: list[dict]
    queries: list[SearchQueryMeta]   


class BarchartResult(pydantic.BaseModel):
    x_axis: str 
    y_axis: str
    data: list[dict]
    queries: list[SearchQueryMeta]   

class SearchMeta(pydantic.BaseModel):
    snippet: typing.Optional[SnippetResult] = None
    table: typing.Optional[TableResult] = None
    barchart: typing.Optional[BarchartResult] = None

class SearchResult(pydantic.BaseModel):
    data: list[SearchData]
    meta: SearchMeta

class Message(pydantic.BaseModel):
    msg: typing.Optional[str]

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