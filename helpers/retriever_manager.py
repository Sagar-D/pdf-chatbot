from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from helpers.vectordb_manager import VectorDBManager
from helpers.doc_cache_manager import DocCacheManager
import constants
from typing import Literal
from sentence_transformers import CrossEncoder

cache_manager = DocCacheManager()


class Retriever:

    def __init__(
        self,
        type: Literal["hybrid", "semantic", "keyword"] = "hybrid",
        max_k: int = constants.VECTOR_RETRIEVER_MAX_DOCS,
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

    def _get_semantic_retriever(self, vectordb_manager: VectorDBManager = None):
        if not vectordb_manager:
            vectordb_manager = VectorDBManager()

        chroma_store = Chroma(
            client=vectordb_manager.db_client,
            collection_name=vectordb_manager.collection_name,
            embedding_function=HuggingFaceEmbeddings(
                model_name=constants.VECTOR_EMBEDDING_MODEL
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
        reranker = CrossEncoder(constants.CROSS_ENCODER_MODEL)
        scores = reranker.predict([(query, doc.page_content) for doc in docs])
        scored_docs = list(zip(docs, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        relevent_docs = []
        for doc, score in scored_docs:
            if score > constants.CROSS_ENCODER_RELEVANCE_THRUSHOLD:
                relevent_docs.append(doc)
                continue
            if len(relevent_docs) > int(self.k * 0.2):
                break
            relevent_docs.append(doc)
        return relevent_docs
