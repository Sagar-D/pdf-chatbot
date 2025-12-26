from pdf_chatbot.rag.rag_agent import RAGAgent
from pdf_chatbot.documents.document_processor import save_user_documents
import base64
from pdf_chatbot import config


def rag_chat(
    session: dict,
    input: str,
    files: list[bytes],
    llm_platform: str = config.LLM_PLATFORMS[0],
):

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


def _ingest_documents(files: list[bytes], user_id: int):
    return save_user_documents(files=files, user_id=user_id)
