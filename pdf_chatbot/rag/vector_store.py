from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from typing import Sequence
import dotenv
import pdf_chatbot.config as config
from langchain_core.documents import Document

dotenv.load_dotenv()
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=config.VECTOR_EMBEDDING_MODEL
)


class VectorStore:

    _vector_store_instances = {}

    @classmethod
    def get_instance(cls, collection_name: str = config.DEFAULT_VECTOR_COLLECTION_NAME):

        collection_name = (
            collection_name.strip() or config.DEFAULT_VECTOR_COLLECTION_NAME
        )

        if collection_name not in cls._vector_store_instances:
            cls._vector_store_instances[collection_name] = cls(collection_name)
        return cls._vector_store_instances[collection_name]

    def __init__(self, collection_name: str = ""):

        if (not collection_name) or collection_name.strip() == "":
            collection_name = config.DEFAULT_VECTOR_COLLECTION_NAME

        self.db_client = PersistentClient(path=config.DEFAULT_VECTOR_DB_PATH)
        self.collection_name = collection_name.strip()
        self.embedding_function = embedding_fn
        self.collection = self.db_client.get_or_create_collection(
            self.collection_name,
            embedding_function=self.embedding_function,
        )

    def add(
        self, ids: Sequence[str], chunks: Sequence[str], metadatas: Sequence[dict]
    ) -> None:
        self.collection.add(ids=ids, documents=chunks, metadatas=metadatas)

    def fetch_similar_docs(
        self, query: str, limit: int = config.VECTOR_RETRIEVER_MAX_DOCS
    ) -> list[Document]:
        results = self.collection.query(query_texts=[query], n_results=limit)
        return results["documents"][0]

    def document_exists(self, metadata_filter: dict) -> bool:
        results = self.collection.get(where=metadata_filter)
        return len(results["documents"]) > 0

    def get_document_chunks(self, metadata_filter: dict) -> list[str]:
        results = self.collection.get(where=metadata_filter)
        return results["documents"]
