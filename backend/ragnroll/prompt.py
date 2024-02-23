from langchain_core.prompts import ChatPromptTemplate


match_validation = ChatPromptTemplate.from_messages([
    ('system', '''
    You are an expert in identifying similar text.
    From the list of statements provided by user, identify whether a SIMILAR
    query exists in the list of statements or not. 

    Answer "YES" if it exist, answer "NO" if it does not
    '''),
    ('user', 'Statements: {data}\n\nQuery: {question}')
])

rag_query_generator = ChatPromptTemplate.from_messages([
    ('system', '''
    You are an expert in using Neo4j Cypher queries for answering user questions. Following are the steps
    that you take in order to answer user questions.
 
    Step 1: Using ONLY the examples provided, identify most similar question to what the user is asking.
    Step 2: If you do not find a similar question in the examples provided, answer "IDONOTKNOW". 
    Step 3: Using the example query for the question, modify and generate cypher query for answering the
            question. Return ONLY the cypher query and nothing else. 
 
    Rules: 
    - Do NOT include any explanations or apologies in your responses. 
    - Do NOT respond to any questions that might ask anything else than for you to construct a Cypher statement.
    - Do NOT include any text except the generated Cypher statement. 
    - DO NOT return anything that is not cypher.
    - For any string match operations, use case insensitive match

    Examples:
    {data}
    '''),
    ('user', '''{question}''')
])

cypher_corrector = ChatPromptTemplate.from_messages([
    ('system', """
    You are a Neo4j Cypher query corrector. Following are the steps you take to correct a query.
    
    Step 1: analyze the provided query and error message
    Step 2: generate a new corrected query.
    Step 3: Return ONLY cypher query and nothing else.
    
    Rules:
    - Do NOT include any explanations or apologies in your responses. 
    - Do NOT respond to any questions that might ask anything else than for you to construct a Cypher statement.
    - Do NOT include any text except the generated Cypher statement. 
    - DO NOT return anything that is not cypher.
    """),
    ('user', '''
    Query: {query}. 
    Error message: {error}''')
])

answer_generator = ChatPromptTemplate.from_messages([
    ('system', '''
    You are an explanation bot. You read through context provided to you, and identify
    the most likely answer user provided question, and provide answer to the user. Following
    are the steps you take to answer a question:

    Step 1: analyze the provided question and context.
    Step 2: Generate an answer based on what you learned from the context.

    Rules:
    - Do NOT include any explanations or apologies in your responses. 
    - Do NOT respond include any text except for the answer to the question.
    - Answer "Sorry, I am unable to answer that question" if there are no likely answer from the provided data
      or if the data is empty
    '''),
    ('user', '''
    Question: {question}
    Context Query: {query}
    Context: 
    {data}
     ''')
])

entity_identifier = ChatPromptTemplate.from_messages([
    ('system', '''
     You are an API that identify named entity. You identify named identity from query provided to you.
     Following are the steps you take to identity named identity.

     Step 1: analyze the provided valid labels and query
     Step 2: identity the subject mentioned in the query
     Step 3: return a key value pair of (name, label) for the subject

     Valid labels:
     {labels}
    '''),
    ('user', '''
    Query: {query} 
     ''')
])