# RAG configs
VECTOR_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_RETRIEVER_MAX_DOCS = 10
DEFAULT_VECTOR_DB_PATH=".chroma/"
DEFAULT_VECTOR_COLLECTION_NAME = "pdf-chatbot-collection"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CROSS_ENCODER_RELEVANCE_THRUSHOLD = 0


# LLM configs
LLM_PLATFORMS = ["ollama", "gemini"]
DEFAULT_LLM_MODELS = {"ollama": "qwen3:3b", "gemini": "gemini-2.0-flash"}
QUERY_ENRICHMENT_MODEL = {"ollama": "qwen2.5:3b", "gemini": "gemini-2.5-flash-lite"}
ELIGIBILITY_CHECK_MODEL = {"ollama": "qwen2.5:3b", "gemini": "gemini-2.5-flash-lite"}
RESPONSE_GENERATOR_MODEL = {"ollama": "qwen3:8b", "gemini": "gemini-2.0-flash"}

## RAG Agent configs
PROMPT_ENRICHMENT_FEATURE_ENABLED=False
IS_CONVERSATIONAL_RAG=False

