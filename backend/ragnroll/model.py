import pydantic
import enum
import typing
import neo4j
from .crud.model import *
from .crud.collection import NodeCollection
from .crud.view import NodeCollectionEndpoints
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

class QueryType(enum.StrEnum):
   CYPHER = 'cypher'

class VisualizationType(enum.StrEnum):
    TEXT_ANSWER = 'text-answer'
    BAR_CHART = 'bar-chart'

class RetrievalQuestion(pydantic.BaseModel):
    question: str

class RetrievalQuery(pydantic.BaseModel):
    query: str
    query_type: QueryType = 'cypher'
    visualization: VisualizationType = 'text-answer'


class Document(pydantic.BaseModel):
    title: typing.Optional[str]
    description: typing.Optional[str]
    file_name: str
    file_size: int
    file_type: str
    file_checksum: str

async def enrich_embedding(txn: neo4j.AsyncTransaction, collection: NodeCollection[RetrievalQuestion], node_id: int, item: RetrievalQuestion):
    embeddings = OpenAIEmbeddings()
    embedding = await embeddings.aembed_query(item.question)
    await txn.run('''
    MATCH (question:RetrievalQuestion) WHERE id(question) = $__node_id
    SET question.embedding = $embedding
    ''', parameters={
        '__node_id': node_id,
        'embedding': embedding
    })

async def cascade_delete(txn: neo4j.AsyncTransaction, collection: NodeCollection[RetrievalQuestion], node_id: int):
    await txn.run('''
    MATCH (q:RetrievalQuestion)-[:ANSWERS]-(qr:RetrievalQuery)           
    WHERE id(qr) = $query_id
    DETACH DELETE q
    ''', parameters={
        'query_id': node_id
    })

RetrievalQueryEndpoints = NodeCollectionEndpoints('retrieval_query', 'RetrievalQuery', RetrievalQuery)
RetrievalQuestionEndpoints = NodeCollectionEndpoints('retrieval_question', 'RetrievalQuestion', RetrievalQuestion, 
                                                     after_update=enrich_embedding, 
                                                     after_create=enrich_embedding,
                                                     before_delete=cascade_delete)