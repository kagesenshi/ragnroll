from .crud.view import NodeCollectionEndpoints
from . import model
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from .crud.collection import NodeCollection
from .crud.view import NodeCollectionEndpoints
import neo4j
import fastapi
from .crud import  db

   
#RAGPattern = NodeCollectionEndpoints('retrieval_pattern', '_RAGPattern', model.RAGPattern)
