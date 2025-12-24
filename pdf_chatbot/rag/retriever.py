from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import CrossEncoder
from pdf_chatbot.rag.vector_store import VectorStore
import pdf_chatbot.config as config


reranker = CrossEncoder(config.CROSS_ENCODER_MODEL)
embedding_fn = HuggingFaceEmbeddings(model_name=config.VECTOR_EMBEDDING_MODEL)


class ScopedHybridRetriever:
    """
    Hybrid retriever scoped to a single metadata filter.
    The filter must include user_id and document_hash_id.
    A new instance must be created if scope changes.
    """

    def __init__(
        self,
        metadata_filter: dict,
        max_k: int = config.VECTOR_RETRIEVER_MAX_DOCS,
    ):

        self._validate_metadata_filter(metadata_filter)
        self.k = max_k
        self.metadata_filter = metadata_filter
        self.vector_store: VectorStore = VectorStore.get_instance()
        self.retriever = self._get_hybrid_retriever(self.metadata_filter)

    def _validate_metadata_filter(self, metadata_filter: dict):

        if (
            not metadata_filter
            or type(metadata_filter) != dict
            or len(metadata_filter.keys()) == 0
        ):
            raise ValueError("Missing required field : metadata_filter")

        if "user_id" not in str(metadata_filter):
            raise ValueError("Missing required filter 'user_id' in metadata_filter")
        if "document_hash_id" not in str(metadata_filter):
            raise ValueError(
                "Missing required filter 'document_hash_id' in metadata_filter"
            )

    def _get_bm25_retriever(self, chunks: list[str]):
        bm25_retriever = BM25Retriever.from_texts(chunks)
        bm25_retriever.k = self.k
        return bm25_retriever

    def _get_semantic_retriever(self, metadata_filter: dict | None = None):

        chroma_store = Chroma(
            client=self.vector_store.db_client,
            collection_name=self.vector_store.collection_name,
            embedding_function=embedding_fn,
        )

        retriever_args = {"k": self.k}
        if metadata_filter and len(metadata_filter.keys()) > 0:
            retriever_args["filter"] = metadata_filter
        return chroma_store.as_retriever(
            search_type="similarity", search_kwargs=retriever_args
        )

    def _get_hybrid_retriever(self, metadata_filter: dict):

        vector_retriever = self._get_semantic_retriever(metadata_filter=metadata_filter)
        bm25_retriever = self._get_bm25_retriever(
            chunks=self.vector_store.get_document_chunks(metadata_filter)
        )

        return EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever], weights=[0.6, 0.4]
        )

    def query_docs(self, query: str, k: int = 3):
        docs = self.retriever.invoke(input=query)
        scores = reranker.predict([(query, doc.page_content) for doc in docs])
        scored_docs = list(zip(docs, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        relevent_docs = [
            doc
            for doc, score in scored_docs
            if score >= config.CROSS_ENCODER_RELEVANCE_THRUSHOLD
        ]
        return relevent_docs[:k]
