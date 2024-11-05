import neo4j.time
from .. import db, model, settings
from ..router import router as app
from ..langchain import embeddings_model
from ..rag import answer_question, default_search
from ..util import format_text
from ..model import ChatRequest, ChatResponse, ChatHistory, ChatHistoryMessage, Result, ChatAgent
from ..db import Session
from ..config import settings
from ..authn import Identity
import ollama
import fastapi
import neo4j
from fastapi.responses import StreamingResponse

# TBD: Manage agents as pipelines JSON
AGENTS = [
    ChatAgent(title='Mistral', name='mistral', model='mistral-nemo:12b-instruct-2407-q4_K_M'),
]

def get_model(agent_name: str):
    for a in AGENTS:
        if a.name == agent_name:
            return a.model
    return 'mistral-nemo:12b-instruct-2407-q4_K_M'

async def ollama_chat_stream(chatrequest: ChatRequest):
    
    req = chatrequest.model_dump()
    session = await ollama.AsyncClient().chat(
        model=get_model(chatrequest.model),
        messages=req['messages'],
        stream=True
    )
    async for item in session:
        data = ChatResponse(model=item['model'], message=item['message']).model_dump_json()
        yield f'{data}\n'

async def ollama_chat(chatrequest: ChatRequest):
    req = chatrequest.model_dump()
    result = await ollama.AsyncClient().chat(
        model=get_model(chatrequest.model),
        messages=req['messages'],
    )
    return ChatResponse(model=result['model'], message=result['message'])

@app.post('/chat/v1/completions')
async def chat(chatrequest: ChatRequest, identity: Identity) -> ChatResponse:
    if chatrequest.stream:
        return StreamingResponse(ollama_chat_stream(chatrequest))

    return await ollama_chat(chatrequest)

@app.get('/chat/v1/recent')
async def recent_chats(request: fastapi.Request, session: Session, identity: Identity, limit: int = 20) -> Result[list[ChatHistory]]:
    if limit > 50:
        limit = 50

    async def transaction(txn: neo4j.AsyncTransaction):
        query = """
        MATCH (s:_ChatSession)-[r:CONTAINS]->(m:_ChatMessage)
        WHERE s.owner = $identity and r.owner = $identity and m.owner = $identity
        WITH s, m ORDER BY m.timestamp ASC
        RETURN s as session, collect(m) as messages 
        ORDER BY session.timestamp DESC
        LIMIT $limit
        """

        chats = await txn.run(query, limit=limit, identity=identity.username)
        return (await chats.data(), await chats.consume())
    (query_result, query_summary) = await session.execute_read(transaction)
    result = []
    for c in query_result:
        session = c['session']
        messages = c['messages']
        chat = ChatHistory(
            identifier=session['identifier'],
            title=session['title'],
            timestamp=session['timestamp'].isoformat(),
            history=[
                ChatHistoryMessage(
                    identifier=m['identifier'],
                    timestamp=m['timestamp'].isoformat(),
                    role=m['role'],
                    message=m['message']
                ) for m in messages
            ]
        )
        result.append(chat)
    return {
        'data': result
    }


@app.get('/chat/v1/session/{identifier}')
async def recent_chats(request: fastapi.Request, session: Session, identity: Identity, identifier: str, limit: int = 20) -> Result[ChatHistory]:
    if limit > 50:
        limit = 50

    async def transaction(txn: neo4j.AsyncTransaction):
        query = """
        MATCH (s:_ChatSession {identifier: $identifier})-[r:CONTAINS]->(m:_ChatMessage)
        WHERE s.owner = $identity and r.owner = $identity and m.owner = $identity
        WITH s, m ORDER BY m.timestamp ASC
        RETURN s as session, collect(m) as messages 
        ORDER BY session.timestamp DESC
        LIMIT $limit
        """

        chats = await txn.run(query, limit=limit, identifier=identifier, identity=identity.username)
        return (await chats.single(), await chats.consume())
    (c, query_summary) = await session.execute_read(transaction)
    session = c['session']
    messages = c['messages']
    chat = ChatHistory(
        identifier=session['identifier'],
        title=session['title'],
        timestamp=session['timestamp'].isoformat(),
        history=[
            ChatHistoryMessage(
                identifier=m['identifier'],
                timestamp=m['timestamp'].isoformat(),
                role=m['role'],
                message=m['message']
            ) for m in messages
        ]
    )
    return {
        'data': chat
    }
    


@app.put("/chat/v1/session/{identifier}")
async def put_chat_history(
    request: fastapi.Request, chat: ChatHistory, session: Session,
    identifier: str,
    identity: Identity
):
    
    chat.identifier = identifier
    async def transaction(txn: neo4j.AsyncTransaction):
        await txn.run(
            "MERGE (n:_ChatSession {identifier: $identifier})",
            identifier=chat.identifier,
        )
        await txn.run(
            """
                MATCH (n:_ChatSession {identifier: $identifier}) 
                SET n.title=$title, n.timestamp=datetime($timestamp), n.owner=$identity
                """,
            identifier=chat.identifier,
            title=chat.title,
            timestamp=chat.timestamp,
            identity=identity.username
        )
        prev = None
        for msg in chat.history:
            await txn.run(
                """MERGE (n:_ChatMessage {identifier: $identifier})""",
                identifier=msg.identifier,
            )
            await txn.run(
                """
                    MATCH (n:_ChatMessage {identifier: $identifier})
                    SET n.role=$role, n.message=$message, n.timestamp=datetime($timestamp), n.model=$model, n.owner=$identity
                """,
                identifier=msg.identifier,
                role=msg.role,
                timestamp=msg.timestamp,
                message=msg.message,
                model=msg.model,
                identity=identity.username
            )
            await txn.run(
                """
                    MATCH (chat:_ChatSession {identifier: $chat_identifier})
                    MATCH (msg:_ChatMessage {identifier: $msg_identifier})
                    MERGE (chat)-[:CONTAINS {owner: $identity}]->(msg)
                """,
                chat_identifier=chat.identifier,
                msg_identifier=msg.identifier,
                identity=identity.username
            )
            if prev:
                await txn.run(
                    """
                        MATCH (curr:_ChatMessage {identifier: $curr_id})
                        MATCH (prev:_ChatMessage {identifier: $prev_id})
                        MERGE (prev)-[:FOLLOWED_BY {owner: $identity}]->(curr)
                    """,
                    curr_id=msg.identifier,
                    prev_id=prev.identifier,
                    identity=identity.username
                )
            prev = msg

    await session.execute_write(transaction)

    return {}

@app.delete("/chat/v1/session/{identifier}")
async def delete_chat_history(
    request: fastapi.Request, identifier: str, session: Session,
    identity: Identity
):
    
    async def transaction(txn: neo4j.AsyncTransaction):
        query = """
        MATCH (n:_ChatSession {identifier: $identifier, owner: $identity})
        OPTIONAL MATCH (n)-[:CONTAINS]-(msg:_ChatMessage)
        detach delete n,msg
        """
        await txn.run(
            query,
            identifier=identifier,
            identity=identity.username
        )
    
    await session.execute_write(transaction)

    return {}



@app.get('/model/v1/models')
async def get_agents(request: fastapi.Request, identity: Identity) -> Result[list[ChatAgent]]:
    return {
        'data': AGENTS
    }