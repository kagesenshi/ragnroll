import pydantic
import enum
import typing
import neo4j

NAME_PATTERN=r'^[a-z0-9\-]*$'

T = typing.TypeVar('T', bound=pydantic.BaseModel)

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
    PIE_CHART = 'pie-chart'


class Language(enum.StrEnum):
    en_US = 'en_US'
    ms_MY = 'ms_MY'

class RAGQuestion(pydantic.BaseModel):
    name: str = pydantic.Field(strict=True, pattern=NAME_PATTERN, default='default')
    question: str 
    language: Language = Language.en_US

class NameReference(pydantic.BaseModel):
    name: str = pydantic.Field(strict=True, pattern=NAME_PATTERN)

class RAGQuery(pydantic.BaseModel):
    questions: list[NameReference]  = pydantic.Field(default_factory=lambda : [NameReference(name='default')])
    query: str 

class RAGOutput(pydantic.BaseModel):
    name: str = pydantic.Field(strict=True, pattern=NAME_PATTERN)
    visualization: VisualizationType = VisualizationType.TEXT_ANSWER
    samples: list[RAGQuery]
    order: int = 0

class RAGPattern(pydantic.BaseModel):
    name: str = pydantic.Field(strict=True, pattern=NAME_PATTERN)
    questions: list[RAGQuestion]
    outputs: list[RAGOutput]


class ConfigMetadata(pydantic.BaseModel):
    name: str = pydantic.Field(strict=True, pattern=NAME_PATTERN)

class RAGExpertiseSpec(pydantic.BaseModel):
    patterns: list[RAGPattern]    

class Config(pydantic.BaseModel, typing.Generic[T]):
    kind: str
    metadata: ConfigMetadata
    spec: T

RAGExpertise = Config[RAGExpertiseSpec]

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
    order: int = 0
 
class SearchResult(pydantic.BaseModel):
    data: list[SearchResultItem]
#    meta: SearchMeta