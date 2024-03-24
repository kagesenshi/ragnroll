import fastapi
from . import db
from . import model
from .crud.view import NodeCollectionEndpoints
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

async def retrieval_query_factory(request: fastapi.Request) -> db.RetrievalQuery:
    session = await db.session(request)
    chat = ChatOpenAI()
    embedding = OpenAIEmbeddings()
    collection = db.RetrievalQuery(session, chat, embedding)
    return collection

RetrievalQueryEndpoints = NodeCollectionEndpoints('retrieval_query', model.RetrievalQuery, retrieval_query_factory)

