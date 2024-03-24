from ragnroll import settings
import neo4j
import fastapi
import ssl
import json
import abc
import pydantic
import typing
from . import model
from .crud.collection import NodeCollection
from .crud.db import connect, session
from .crud.view import NodeCollectionEndpoints
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
import asyncio

class RetrievalQuery(NodeCollection[model.RetrievalQuery]):
    def __init__(self, session: neo4j.AsyncSession, chat: BaseChatModel, embeddings: Embeddings):
        self.chat = chat
        self.embeddings = embeddings
        return super().__init__(session, 'RetrievalQuery', model.RetrievalQuery)
    
    async def add_question(self, txn: neo4j.AsyncManagedTransaction, node_id: int, item: model.RetrievalQuestion) -> list[model.Node[model.RetrievalQuestion]]:
        async def _job(txn: neo4j.AsyncTransaction):
            embedding = await self.embeddings.aembed_query(item.question)
            cypher = '''
            MERGE (question:RetrievalQuestion {question: toLower($question)}) 
            MATCH (query:RetrievalQuery) WHERE id(node) == $__node_id
            MERGE (query)-[:ANSWERS]->(question)
            RETURN id(question) as identifier, question, labels(question) as node_labels;

            MATCH (question:RetrievalQuestion {question: toLower($question)})
            SET question.embedding = $embedding;
            '''
            res = await txn.run(cypher, parameters={'__node_id': node_id,
                                                    'question': item.question,
                                                    'embedding': embedding})
            return [model.Node[model.RetrievalQuestion](id=r['identifier'], properties=r['node'], labels=r['node_labels']) for r in res.data()]
        return self.session.execute_write(_job)

    async def match_question(self, txn: neo4j.AsyncTransaction, query: str, count: int =10, min_score: int=0) -> list[model.ScoredNode[model.RetrievalQuestion]]:
        async def _job(txn: neo4j.AsyncTransaction):
           embedding = await self.embeddings.aembed_query(query)
           cypher = '''
           CALL db.index.vector.queryNodes('questions_embedding', $count, $embedding)
           YIELD node, score
           WITH node, score
               WHERE $label in labels(node)
               AND score > $min_score
           RETURN id(node) as identifier, node, labels(node) as node_labels, score
           ''' 
           res = await txn.run(cypher, parameters={'label': self.label, 'embedding': embedding, 'count': count, 'min_score': min_score})
           return [model.ScoredNode[self.schema](id=r['identifier'], properties=r['node'], labels=r['node_labels'], score=r['score']) for r in await res.data()]
        return self.session.execute_read(_job)
    
