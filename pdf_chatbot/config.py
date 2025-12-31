import os
import dotenv
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "/tmp"))

dotenv.load_dotenv()
env = str(os.getenv("PDF_CHATBOT_DEPLOYMENT_ENV")).lower()
is_prod = env == "prod"

# API configs
MAX_FILE_SIZE_MB = 10

# RAG configs
VECTOR_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_RETRIEVER_MAX_DOCS = 10
DEFAULT_VECTOR_DB_PATH = DATA_DIR / ".chroma/"
DEFAULT_VECTOR_COLLECTION_NAME = "pdf-chatbot-collection"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CROSS_ENCODER_RELEVANCE_THRUSHOLD = 0
RAG_DEFAULT_TIMEOUT = 20 if is_prod else 60


# LLM configs
LLM_PLATFORMS = ["gemini"] if is_prod else["ollama", "gemini"] 
DEFAULT_LLM_PLATFORM = "gemini" if is_prod else "ollama"
DEFAULT_LLM_MODELS = {"ollama": "qwen3:8b", "gemini": "gemini-2.0-flash"}
QUERY_ENRICHMENT_MODEL = {"ollama": "qwen2.5:3b", "gemini": "gemini-2.5-flash-lite"}
RESPONSE_GENERATOR_MODEL = {"ollama": "qwen3:8b", "gemini": "gemini-2.0-flash"}
LLM_DEFAULT_TIMEOUT = 20 if is_prod else 60

## RAG Agent configs
QUERY_ENRICHMENT_FEATURE_ENABLED = True if is_prod else False

# Relational Database
RELATIONAL_DB_NAME = DATA_DIR / "accounts.sqlite"
CHAT_HISTORY_ROOT_FOLDER = DATA_DIR / ".chat_history/"
