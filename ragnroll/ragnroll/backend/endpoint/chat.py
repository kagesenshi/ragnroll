from .. import db, model, settings
from ..router import router as app
from ..langchain import embeddings_model
from ..rag import answer_question, default_search
from ..util import format_text
from ..model import ChatRequest, ChatResponse
from ..config import settings
import ollama
import fastapi
from fastapi.responses import StreamingResponse

async def ollama_chat_stream(chatrequest: ChatRequest):
    req = chatrequest.model_dump()
    session = await ollama.AsyncClient().chat(
        model=chatrequest.model,
        messages=req['messages'],
        stream=True
    )

    async for item in session:
        data = ChatResponse(model=item['model'], message=item['message']).model_dump_json()
        yield f'{data}\n'

async def ollama_chat(chatrequest: ChatRequest):
    req = chatrequest.model_dump()
    result = await ollama.AsyncClient().chat(
        model=chatrequest.model,
        messages=req['messages'],
    )
    return ChatResponse(model=result['model'], message=result['message'])

@app.post('/chat')
async def chat(chatrequest: ChatRequest) -> ChatResponse:
    if chatrequest.stream:
        return StreamingResponse(ollama_chat_stream(chatrequest))

    return await ollama_chat(chatrequest)