import pydantic
import enum
import typing
import neo4j

NAME_PATTERN=r'^[a-z0-9\-]*$'

T = typing.TypeVar('T', bound=pydantic.BaseModel)
M = typing.TypeVar('M', bound=pydantic.BaseModel)


class SearchParam(pydantic.BaseModel):
    question: str

class SearchData(pydantic.BaseModel):
    title: str
    match: str
    url: pydantic.AnyHttpUrl

class SearchMeta(pydantic.BaseModel):
    pass 

class Message(pydantic.BaseModel):
    message: str

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
    title: typing.Optional[str] = None

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

class Error(pydantic.BaseModel):
    detail: typing.Optional[str] = None
    status: typing.Optional[int] = pydantic.Field(default=None)
    code: typing.Optional[str] = pydantic.Field(default=None)
    meta: typing.Optional[dict] = pydantic.Field(default=None)

class ErrorResult(pydantic.BaseModel):
    detail: typing.Optional[str] = None
    errors: typing.Optional[list[Error]] = pydantic.Field(default_factory=list)

class Links(pydantic.BaseModel):
    self: str 
    next: typing.Optional[str] = None
    prev: typing.Optional[str] = None
    
class ResultModel(ErrorResult, typing.Generic[T]):
    data: T
    links: typing.Optional[Links] = None

class ExtendedResultModel(ResultModel, typing.Generic[T, M]):
    meta: M

class Result(ErrorResult, typing.Generic[T]):
    data: typing.Union[list[T], T]
    links: typing.Optional[Links] = None

class ExtendedResult(Result, typing.Generic[T, M]):
    meta: M

class SearchResult(Result[list[SearchResultItem]]):
    pass

class ChatMessage(pydantic.BaseModel):
    role: str
    content: str

class ChatRequest(pydantic.BaseModel):
    model: str 
    messages: list[ChatMessage]
    stream: bool = False

class ChatResponse(pydantic.BaseModel):
    model: str
    message: ChatMessage

class ChatHistoryMessage(pydantic.BaseModel):
    identifier: str
    timestamp: str
    role: str 
    message: str 

class ChatHistory(pydantic.BaseModel):
    identifier: str 
    title: str 
    timestamp: str
    history: list[ChatHistoryMessage]


class OIDCConfiguration(pydantic.BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    response_types_supported: list[str]
    subject_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]
    scopes_supported: list[str]
    token_endpoint_auth_methods_supported: list[str]
    claims_supported: list[str]

class RealmAccess(pydantic.BaseModel):
    roles: list[str] | None

class ResourceAccess(pydantic.BaseModel):
    roles: list[str] | None

class OIDCAccessToken(pydantic.BaseModel):
    exp: int | None = None
    iat: int | None = None
    jti: str | None = None
    iss: str | None = None
    aud: str | None = None
    sub: str | None = None
    typ: str | None = None
    azp: str | None = None
    session_state: str | None = None
    acr: str | None = None
    allowed_origins: list[str] | None = None
    realm_access: RealmAccess | None = None
    resource_access: dict[str, ResourceAccess] | None = None
    scope: str | None = None
    sid: str | None = None
    email_verified: bool | None = None
    roles: list[str] | None = pydantic.Field(None, validation_alias=pydantic.AliasChoices('roles','groups'))
    name: str | None = None
    preferred_username: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    email: str | None = None