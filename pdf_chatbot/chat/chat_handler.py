from pdf_chatbot.rag.rag_agent import RAGAgent
from pdf_chatbot.documents.document_processor import save_user_documents
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import Runnable
from pdf_chatbot import config
from pdf_chatbot.llm.prompt_templates import SIMPLE_CHAT_PROMPT_TEMPLATE
from pdf_chatbot.llm.model_manager import get_llm_instance


def rag_chat(
    session: dict,
    input: str,
    files: list[bytes],
    llm_platform: str = config.LLM_PLATFORMS[0],
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

    chat_history = session["chat_history"] or []
    state = {
        "input": input,
        "llm_platform": llm_platform,
        "user_id": session["user_id"],
        "messages": chat_history,
    }
    document_hash_ids = _ingest_documents(files, session.get("user_id"))
    state["active_documents_hash_list"] = document_hash_ids

    agent = RAGAgent()
    result_state = agent.invoke(state)
    return result_state["messages"]


def simple_chat(
    session: dict, input: str, llm_platform: str = config.LLM_PLATFORMS[0]
) -> list[BaseMessage]:

    chat_history = session.get("chat_history") or []
    chain: Runnable = SIMPLE_CHAT_PROMPT_TEMPLATE | get_llm_instance(
        platform=llm_platform
    )
    response = chain.invoke({"input": input, "messages": chat_history})
    chat_history.append(HumanMessage(content=input))
    chat_history.append(response)
    return chat_history


def smart_chat(
    session: dict,
    input: str,
    files: list[bytes] | None = None,
    llm_platform: str = config.LLM_PLATFORMS[0],
) -> list[BaseMessage]:
    if not files or type(files) != list or len(files) == 0:
        return simple_chat(session=session, input=input, llm_platform=llm_platform)
    else:
        return rag_chat(
            session=session, input=input, files=files, llm_platform=llm_platform
        )


def _ingest_documents(files: list[bytes], user_id: int):
    return save_user_documents(files=files, user_id=user_id)
