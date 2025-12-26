from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import dotenv
from pdf_chatbot import config

dotenv.load_dotenv()


def _get_ollama_instance(model: str | None = None):
    if not model:
        model = config.DEFAULT_LLM_MODELS["ollama"]
    return ChatOllama(base_url=os.getenv("OLLAMA_BASE_URL"), model=model)


def _get_gemini_instance(model: str | None = None):
    if not model:
        model = config.DEFAULT_LLM_MODELS["gemini"]
    return ChatGoogleGenerativeAI(
        model=model, google_api_key=os.getenv("GOOGLE_API_KEY")
    )


def get_llm_instance(platform: str, model: str = None):
    if platform.strip().lower() == "gemini":
        return _get_gemini_instance(model)
    if platform.strip().lower() == "ollama":
        return _get_ollama_instance(model)
    raise ValueError(
        f"Unsupported LLM platform passed. Supported LLM platforms : {config.LLM_PLATFORMS}"
    )
