from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import dotenv

dotenv.load_dotenv()
ollama_llm = ChatOllama(
    base_url=os.getenv("OLLAMA_BASE_URL"), model=os.getenv("OLLAMA_MODEL")
)

gemini_llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL"), google_api_key=os.getenv("GOOGLE_API_KEY")
)


def get_llm_instance(platform: str = "ollama"):
    if platform.strip() == "gemini":
        return gemini_llm
    return ollama_llm
