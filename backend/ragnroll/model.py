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

class SearchMeta(pydantic.BaseModel):
    pass 

class Message(pydantic.BaseModel):
    msg: str

class QueryType(enum.StrEnum):
   CYPHER = 'cypher'

class VisualizationType(enum.StrEnum):
    TEXT_ANSWER = 'text-answer'
    BAR_CHART = 'bar-chart'
    LINE_CHART = 'line-chart'
    TABLE = 'table'


class Language(enum.StrEnum):
    en_US = 'en_US'
    ms_MY = 'ms_MY'

class RAGQuestion(pydantic.BaseModel):
    question: str 
    language: Language = Language.en_US

class RAGAnswer(pydantic.BaseModel):
    query: str 
    visualization: VisualizationType = VisualizationType.TEXT_ANSWER

class RAGPattern(pydantic.BaseModel):
    name: str = pydantic.StringConstraints(strip_whitespace=True, strict=True, pattern=r'^[a-z0-9\-]*$')
    questions: list[RAGQuestion]
    answers: list[RAGAnswer]


class ConfigMetadata(pydantic.BaseModel):
    name: str = pydantic.StringConstraints(strip_whitespace=True, strict=True, pattern=r'^[a-z0-9\-]*$')

class RAGExpertise(pydantic.BaseModel):
    metadata: ConfigMetadata
    patterns: list[RAGPattern] 

class Axes(pydantic.BaseModel):
    x: typing.Optional[str] = None
    y: typing.Optional[str] = None
    z: typing.Optional[str] = None

class SearchQueryMeta(pydantic.BaseModel):
    query: str
    result: str

class SearchResultItem(pydantic.BaseModel):
    data: list[dict]
    queries: list[SearchQueryMeta]    
    visualization: VisualizationType
    fields: list[str]
    axes: Axes = pydantic.Field(default_factory=Axes)
 
class SearchResult(pydantic.BaseModel):
    data: list[SearchResultItem]
#    meta: SearchMeta