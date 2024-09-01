import fastapi
import yaml.parser

from . import model
from .langchain import chat_model
import neo4j.exceptions
from .util import extract_model
import asyncio
import neo4j.spatial
import neo4j.time
import neo4j.graph
import yaml
import yaml.parser
import pydantic
from fastapi_yaml import YamlRoute
import fastapi.exceptions

from ..ragnroll import app as reflex_app

router = fastapi.APIRouter(route_class=YamlRoute, responses={422: {
    'description': 'Validation Error',
    'model': model.ErrorResult
}})

reflex_app.api.title = "RAG'n'Roll"

@router.post("/chat/completions", response_model_exclude_none=True, response_model_exclude_unset=True)
async def chat():
    pass

@reflex_app.api.exception_handler(yaml.parser.ParserError)
async def parser_error(exc: yaml.parser.ParserError, request: fastapi.Request, response: fastapi.Response) -> model.ErrorResult:
    response.status_code = 422
    return model.ErrorResult(
        errors=[model.Error(default='Invalid data type')]
    )

@reflex_app.api.exception_handler(fastapi.HTTPException)
async def http_exc(exc: fastapi.HTTPException, response: fastapi.Response) -> model.ErrorResult:
    response.status_code = exc.status_code
    return model.ErrorResult(
        errors=[model.Error(detail=exc.detail)]
    )

@reflex_app.api.exception_handler(pydantic.ValidationError)
async def pydantic_validation_exc(exc: pydantic.ValidationError, response: fastapi.Response) -> model.ErrorResult:
    response.status_code = 422
    return model.ErrorResult(
        errors=[model.Error(detail=e.msg, meta={'raw': e}) for e in exc.errors()]
    )

@reflex_app.api.exception_handler(fastapi.exceptions.RequestValidationError)
async def fastapi_validation_exc(exc: fastapi.exceptions.RequestValidationError,  response: fastapi.Response) -> model.ErrorResult:
    response.status_code = 422
    return model.ErrorResult(
        errors=[model.Error(detail=e.msg, meta={'raw': e}) for e in exc.errors()]
    )