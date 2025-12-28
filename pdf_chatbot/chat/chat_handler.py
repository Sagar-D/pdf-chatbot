from pdf_chatbot.rag.rag_agent import RAGAgent
from pdf_chatbot.documents.document_processor import (
    verify_user_documents,
    save_user_documents,
)
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import Runnable
from pdf_chatbot import config
from pdf_chatbot.llm.prompt_templates import SIMPLE_CHAT_PROMPT_TEMPLATE
from pdf_chatbot.llm.model_manager import get_llm_instance_async
from pdf_chatbot.schemas.agent import AgentConfig, RAGAgentState


async def rag_chat(
    session: dict,
    input: str,
    files: list[bytes],
    agent_config: AgentConfig | None = AgentConfig(),
) -> list[BaseMessage]:

    if not session or type(session) != dict:
        raise ValueError("Missing or Invalid required parameter 'session'")
    if "user_id" not in session or type(session["user_id"]) != int:
        raise ValueError("Required key 'user_id' not found in 'session'")
    if not input or type(input) != str or input.strip() == "":
        raise ValueError("Missing or Invalid required parameter 'input'")
    if not files or type(files) != list or len(files) == 0:
        raise ValueError(
            "Missing or Invalid required parameter 'files' for PDF RAG chat"
        )

    document_hash_ids = await _ingest_documents(files, session.get("user_id"))

    agent_state = RAGAgentState(
        user_id=int(session["user_id"]),
        input=input,
        messages=session["chat_history"] or [],
        active_documents_hash_list=document_hash_ids,
        config=agent_config,
    )
    agent = RAGAgent()
    result_state = await agent.ainvoke(state=agent_state)
    return result_state["messages"]


async def simple_chat(
    session: dict, input: str, llm_platform: str = config.DEFAULT_LLM_PLATFORM
) -> list[BaseMessage]:

    chat_history = session.get("chat_history") or []
    chain: Runnable = SIMPLE_CHAT_PROMPT_TEMPLATE | await get_llm_instance_async(
        platform=llm_platform
    )
    response = await chain.ainvoke({"input": input, "messages": chat_history})
    chat_history.append(HumanMessage(content=input))
    chat_history.append(response)
    return chat_history


async def smart_chat(
    session: dict,
    input: str,
    files: list[bytes] | None = None,
    agent_config: AgentConfig = AgentConfig(),
) -> list[BaseMessage]:
    if not files or type(files) != list or len(files) == 0:
        return await simple_chat(
            session=session, input=input, llm_platform=agent_config.llm_platform
        )
    else:
        return await rag_chat(
            session=session, input=input, files=files, agent_config=agent_config
        )


async def _ingest_documents(files: list[bytes], user_id: int):
    verify_user_documents(files=files)
    return await save_user_documents(files=files, user_id=user_id)
