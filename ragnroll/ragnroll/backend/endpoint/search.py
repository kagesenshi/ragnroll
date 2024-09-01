from .. import db, model, settings
from ..router import router as app
from ..langchain import embeddings_model
from ..rag import answer_question, default_search
from ..util import format_text

import fastapi


async def _search(request: fastapi.Request, question: str) -> model.SearchResult:
    print(format_text(f"> Searching: '{question}'", bold=True))
    print(format_text("> Entering embedding calculation", bold=True))
    embedding = await embeddings_model.aembed_query(question)
    print(format_text("> Embedding done", bold=True))
    driver = db.connect(request)
    answers = await answer_question(question, embedding=embedding, driver=driver)
    if not answers and settings.ALLOW_FALLBACK:
        answers = await default_search(question, driver=driver)
    return model.SearchResult(data=answers)


# Search
@app.get("/search", response_model_exclude_none=True, response_model_exclude_unset=True)
async def search(request: fastapi.Request, question: str) -> model.SearchResult:
    return await _search(request, question)


@app.post("/search", response_model_exclude_none=True, response_model_exclude_unset=True)
async def post_search(request: fastapi.Request, payload: model.SearchParam) -> model.SearchResult:
    return await _search(request, payload.question)