import os
import dotenv

dotenv.load_dotenv()
env = str(os.getenv("PDF_CHATBOT_DEPLOYMENT_ENV")).lower()

# API configs
MAX_FILE_SIZE_MB = 10

# RAG configs
VECTOR_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_RETRIEVER_MAX_DOCS = 10
DEFAULT_VECTOR_DB_PATH = ".chroma/"
DEFAULT_VECTOR_COLLECTION_NAME = "pdf-chatbot-collection"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CROSS_ENCODER_RELEVANCE_THRUSHOLD = 0
RAG_DEFAULT_TIMEOUT = 20 if env == "prod" else 60


# LLM configs
LLM_PLATFORMS = ["ollama", "gemini"]
DEFAULT_LLM_PLATFORM = "gemini" if env == "prod" else "ollama"
DEFAULT_LLM_MODELS = {"ollama": "qwen3:8b", "gemini": "gemini-2.0-flash"}
QUERY_ENRICHMENT_MODEL = {"ollama": "qwen2.5:3b", "gemini": "gemini-2.5-flash-lite"}
RESPONSE_GENERATOR_MODEL = {"ollama": "qwen3:8b", "gemini": "gemini-2.0-flash"}
LLM_DEFAULT_TIMEOUT = 20 if env == "prod" else 60

## RAG Agent configs
PROMPT_ENRICHMENT_FEATURE_ENABLED = False
IS_CONVERSATIONAL_RAG = False

# Relational Database
RELATIONAL_DB_NAME = "accounts.sqlite"
CHAT_HISTORY_ROOT_FOLDER = ".chat_history/"
