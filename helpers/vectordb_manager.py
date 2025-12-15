from chromadb import Client
from chromadb.utils import embedding_functions
import constants
import dotenv
from typing import Sequence

dotenv.load_dotenv()
DEFAULT_COLLECTION_NAME = "pdf-chatbot-collection"


class VectorDBManager:

    def __init__(self, collection_name: str = ""):

        if (not collection_name) or collection_name.strip() == "":
            collection_name = DEFAULT_COLLECTION_NAME

        self.db_client = Client()
        self.collection_name = collection_name.strip()
        self.embedding_function = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=constants.VECTOR_EMBEDDING_MODEL
            )
        )
        self.collection = self.db_client.get_or_create_collection(
            self.collection_name,
            embedding_function=self.embedding_function,
        )

    def add(self, ids: Sequence[str], chunks: Sequence[str], metadatas: Sequence[dict]):
        self.collection.add(ids=ids, documents=chunks, metadatas=metadatas)
        self.collection.get()

    def fetch_similar_docs(self, query: str, limit: int = constants.VECTOR_RETRIEVER_MAX_DOCS):
        results = self.collection.query(query_texts=[query], n_results=limit)
        return results["documents"]
