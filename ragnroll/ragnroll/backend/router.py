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
from typing import Annotated
from fastapi.security.oauth2 import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from . import exc

from ..ragnroll import app as reflex_app

router = fastapi.APIRouter(route_class=YamlRoute, responses={422: {
    'description': 'Validation Error',
    'model': model.ErrorResult
}})

reflex_app.api.title = "RAG'n'Roll"

@reflex_app.api.exception_handler(yaml.parser.ParserError)
async def parser_error(request: fastapi.Request, exc: yaml.parser.ParserError) -> model.ErrorResult:
    return JSONResponse(content=model.ErrorResult(
        detail='Unable to parse YAML',
        errors=[model.Error(detail='Invalid data type')]
    ).model_dump(), status_code=422)

@reflex_app.api.exception_handler(fastapi.HTTPException)
async def http_exc(request: fastapi.Request, exc: fastapi.HTTPException) -> model.ErrorResult:
    return JSONResponse(content=model.ErrorResult(
        detail=exc.detail,
        errors=[model.Error(detail=exc.detail)]
    ).model_dump(), status_code=exc.status_code)

@reflex_app.api.exception_handler(exc.Unauthorized)
async def unauthorized_exc(request: fastapi.Request, exc: exc.Unauthorized):
    return JSONResponse(content=model.ErrorResult(
        detail=str(exc),
        errors=[model.Error(detail=str(exc))]
    ).model_dump(), status_code=401)

@reflex_app.api.exception_handler(fastapi.exceptions.RequestValidationError)
async def fastapi_validation_exc(request: fastapi.Request, exc: fastapi.exceptions.RequestValidationError):
    return JSONResponse(content=model.ErrorResult(
        detail='Data validation error',
        errors=[model.Error(detail=e['msg'], meta={'raw': e}) for e in exc.errors()]
    ).model_dump(), status_code=422)