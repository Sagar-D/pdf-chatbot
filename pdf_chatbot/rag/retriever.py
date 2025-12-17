from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import Literal
from sentence_transformers import CrossEncoder

from pdf_chatbot.rag.vector_store import VectorStore
from pdf_chatbot.documents.document_processor import DocCacheManager
import pdf_chatbot.config as config


cache_manager = DocCacheManager()


class Retriever:

    def __init__(
        self,
        type: Literal["hybrid", "semantic", "keyword"] = "hybrid",
        max_k: int = config.VECTOR_RETRIEVER_MAX_DOCS,
    ):
        self.k = max_k
        if type == "semantic":
            self.retreiver = self._get_semantic_retriever()
        elif type == "keyword":
            self.retreiver = self._get_bm25_retriever()
        else:
            self.retreiver = self._get_hybrid_retriever()

    def _get_bm25_retriever(self):
        bm25_retriever = BM25Retriever.from_texts(
            cache_manager.get_all_chunks(),
        )
        bm25_retriever.k = self.k
        return bm25_retriever

    def _get_semantic_retriever(self, vector_store: VectorStore = None):
        if not vector_store:
            vector_store = VectorStore()

        chroma_store = Chroma(
            client=vector_store.db_client,
            collection_name=vector_store.collection_name,
            embedding_function=HuggingFaceEmbeddings(
                model_name=config.VECTOR_EMBEDDING_MODEL
            ),
        )
        return chroma_store.as_retriever(
            search_type="similarity", search_kwargs={"k": self.k}
        )

    def _get_hybrid_retriever(
        self, retriever_list: list = [], weights: list[float] = []
    ):
        if len(retriever_list) == 0:
            retriever_list = [
                self._get_semantic_retriever(),
                self._get_bm25_retriever(),
            ]
        if len(weights) == 0:
            weights = [0.6, 0.4]
        return EnsembleRetriever(retrievers=retriever_list, weights=weights)

    def query_docs(self, query: str):

        docs = self.retreiver.invoke(input=query)
        reranker = CrossEncoder(config.CROSS_ENCODER_MODEL)
        scores = reranker.predict([(query, doc.page_content) for doc in docs])
        scored_docs = list(zip(docs, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        relevent_docs = []
        for doc, score in scored_docs:
            if score > config.CROSS_ENCODER_RELEVANCE_THRUSHOLD:
                relevent_docs.append(doc)
                continue
            if len(relevent_docs) > int(self.k * 0.2):
                break
            relevent_docs.append(doc)
        return relevent_docs
