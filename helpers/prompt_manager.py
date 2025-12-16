from langchain_core.prompts import ChatPromptTemplate

QUERY_ELIGIBILITY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You analyze whether user query can be answered using only the given context and not using your internal knowldge.
You respond with
- True : if query is answerable only with provided context. (without using internal knowledge)
- False : if query is not answerable using the context provided, even if you can answer with your internal knowledge.
""",
        ),
        ("user", "Query : {input}\n\nContext : {context}"),
    ]
)

ANSWER_USER_QUERY_PROMPT = QUERY_ELIGIBILITY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an hellpful assistant who can answer user queries based on provided context.
- You always base your answers from the provided context.
- You NEVER USE your internal knowledge for answering user queries.
- You NEVER HALLUCINATE the answers.
- If context is not provided or the provided context is not enough to answer user query, you respond by saying 
    Response : "I don't have enough context to answer your question. Please ask a different query or provide additional context"
""",
        ),
        ("user", "Query : {input}\n\nContext : {context}"),
    ]
)
