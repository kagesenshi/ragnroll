from langchain_core.utils.input import get_colored_text, print_text, get_bolded_text
import typing
import fastapi
import json 
import pydantic
import yaml

def format_text(text, *, color=None, bold=False):
    if color:
        text = get_colored_text(text, color)
    if bold:
        text = get_bolded_text(text)
    return text

S = typing.TypeVar('S', bound=pydantic.BaseModel)

async def extract_model(schema: type[S], request: fastapi.Request) -> S:
    content_type = request.headers.get('Content-Type')
    if content_type.lower() in ['application/yaml', 'text/x-yaml', 'application/x-yaml']:
        config_yaml = (await request.body()).decode('utf-8')
        config_json = json.dumps(yaml.safe_load(config_yaml))
    elif content_type.lower() in ['application/json', 'text/json']:
        config_json = await request.body()
    return schema.model_validate_json(config_json)