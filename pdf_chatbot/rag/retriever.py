from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from typing import Literal
from sentence_transformers import CrossEncoder

from pdf_chatbot.rag.vector_store import VectorStore
from pdf_chatbot.documents.document_processor import DocCacheManager
import pdf_chatbot.config as config


cache_manager = DocCacheManager()
reranker = CrossEncoder(config.CROSS_ENCODER_MODEL)
embedding_fn = HuggingFaceEmbeddings(model_name=config.VECTOR_EMBEDDING_MODEL)


class Retriever:

    def __init__(
        self,
        type: Literal["hybrid", "semantic", "keyword"] = "hybrid",
        max_k: int = config.VECTOR_RETRIEVER_MAX_DOCS,
        file_hash_list: list[str] = None,
    ):
        self.k = max_k
        self.type = type
        self.file_hash_list = file_hash_list or []
        if type == "semantic":
            self.retriever = self._get_semantic_retriever(file_hash_list=file_hash_list)
        elif type == "keyword":
            self.retriever = self._get_bm25_retriever(file_hash_list=file_hash_list)
        else:
            self.retriever = self._get_hybrid_retriever(file_hash_list=file_hash_list)

    def _get_bm25_retriever(self, file_hash_list=None):
        bm25_retriever = BM25Retriever.from_texts(
            cache_manager.get_all_chunks(file_hash_list),
        )
        bm25_retriever.k = self.k
        return bm25_retriever

    def _get_semantic_retriever(
        self, vector_store: VectorStore = None, file_hash_list: list[str] = []
    ):
        if not vector_store:
            vector_store = VectorStore.get_instance()

        retriever_args = {"k": self.k}
        if file_hash_list and len(file_hash_list) > 0:
            retriever_args["filter"] = {"file_hash": {"$in": file_hash_list}}

        chroma_store = Chroma(
            client=vector_store.db_client,
            collection_name=vector_store.collection_name,
            embedding_function=embedding_fn,
        )
        return chroma_store.as_retriever(
            search_type="similarity", search_kwargs=retriever_args
        )

    def _get_hybrid_retriever(
        self,
        retriever_list: list = [],
        weights: list[float] = [],
        file_hash_list: list[str] = None,
    ):
        if len(retriever_list) == 0:
            retriever_list = [
                self._get_semantic_retriever(file_hash_list=file_hash_list),
                self._get_bm25_retriever(file_hash_list=file_hash_list),
            ]
        if len(weights) == 0:
            weights = [0.6, 0.4]
        return EnsembleRetriever(retrievers=retriever_list, weights=weights)

    def query_docs(self, query: str, metadata_filter: dict, k: int = 3):
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
