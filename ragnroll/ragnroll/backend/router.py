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
from fastapi.responses import JSONResponse


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
async def parser_error(request: fastapi.Request, exc: yaml.parser.ParserError, response: fastapi.Response) -> model.ErrorResult:
    response.status_code = 422
    return model.ErrorResult(
        detail='Unable to parse YAML',
        errors=[model.Error(detail='Invalid data type')]
    )

@reflex_app.api.exception_handler(fastapi.HTTPException)
async def http_exc(request: fastapi.Request, exc: fastapi.HTTPException, response: fastapi.Response) -> model.ErrorResult:
    response.status_code = exc.status_code
    return model.ErrorResult(
        detail=exc.detail,
        errors=[model.Error(detail=exc.detail)]
    )

#@reflex_app.api.exception_handler(pydantic.ValidationError)
#async def pydantic_validation_exc(request: fastapi.Request, exc: pydantic.ValidationError):
#    return JSONResponse(content=model.ErrorResult(
#        detail='Data validation error',
#        errors=[model.Error(detail=e['msg'], meta={'raw': e}) for e in exc.errors()]
#    ).model_dump(), status_code=422)

@reflex_app.api.exception_handler(fastapi.exceptions.RequestValidationError)
async def fastapi_validation_exc(request: fastapi.Request, exc: fastapi.exceptions.RequestValidationError) -> model.ErrorResult:
    return JSONResponse(content=model.ErrorResult(
        detail='Data validation error',
        errors=[model.Error(detail=e['msg'], meta={'raw': e}) for e in exc.errors()]
    ).model_dump(), status_code=422)