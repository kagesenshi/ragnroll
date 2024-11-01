import neo4j.time
from .. import db, model, settings
from ..router import router as app
from ..langchain import embeddings_model
from ..rag import answer_question, default_search
from ..util import format_text
from ..model import ChatRequest, ChatResponse, ChatHistory, ChatHistoryMessage, Result
from ..db import Session
from ..config import settings
from ..authn import Identity
import ollama
import fastapi
import neo4j
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

@app.post('/chat/completion')
async def chat(chatrequest: ChatRequest) -> ChatResponse:
    if chatrequest.stream:
        return StreamingResponse(ollama_chat_stream(chatrequest))

    return await ollama_chat(chatrequest)

@app.get('/chat/recent')
async def recent_chats(request: fastapi.Request, session: Session, identity: Identity) -> Result[list[ChatHistory]]:
    async def transaction(txn: neo4j.AsyncTransaction):
        query = """
        MATCH (s:_ChatSession)-[:CONTAINS]->(m:_ChatMessage)
        RETURN s as session, collect(m) as messages 
        ORDER BY session.timestamp DESC
        LIMIT 20
        """
        chats = await txn.run(query)
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
    


@app.put("/chat/session/{identifier}")
async def put_chat_history(
    request: fastapi.Request, chat: ChatHistory, session: Session
):
    async def transaction(txn: neo4j.AsyncTransaction):
        await txn.run(
            "MERGE (n:_ChatSession {identifier: $identifier})",
            identifier=chat.identifier,
        )
        await txn.run(
            """
                MATCH (n:_ChatSession {identifier: $identifier}) 
                SET n.title=$title, n.timestamp=datetime($timestamp)
                """,
            identifier=chat.identifier,
            title=chat.title,
            timestamp=chat.timestamp
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
                    SET n.role=$role, n.message=$message, n.timestamp=datetime($timestamp)
                """,
                identifier=msg.identifier,
                role=msg.role,
                timestamp=msg.timestamp,
                message=msg.message,
            )
            await txn.run(
                """
                    MATCH (chat:_ChatSession {identifier: $chat_identifier})
                    MATCH (msg:_ChatMessage {identifier: $msg_identifier})
                    MERGE (chat)-[:CONTAINS]->(msg)
                """,
                chat_identifier=chat.identifier,
                msg_identifier=msg.identifier,
            )
            if prev:
                await txn.run(
                    """
                        MATCH (curr:_ChatMessage {identifier: $curr_id})
                        MATCH (prev:_ChatMessage {identifier: $prev_id})
                        MERGE (prev)-[:FOLLOWED_BY]->(curr)
                    """,
                    curr_id=msg.identifier,
                    prev_id=prev.identifier,
                )
            prev = msg

    await session.execute_write(transaction)
