from docling.document_converter import DocumentConverter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pdf_chatbot.documents.cache_manager import DocCacheManager
from pdf_chatbot.rag.vector_store import VectorStore
import hashlib

cache_manager = DocCacheManager()
vector_store = VectorStore.get_instance()


class DocumentProcessor:

    def _convert_to_markdown(self, file_path: str):
        doc_converter = DocumentConverter()
        result = doc_converter.convert(source=file_path)
        markdown = result.document.export_to_markdown()
        return markdown

    def _chunk_mardown_doc(self, markdown: str):
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2")]
        )
        chunks = splitter.split_text(markdown)
        return chunks

    def _generate_hash(self, content: str):
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _doc_exists_in_cache(self, file_content: str):
        hash = self._generate_hash(file_content)
        if cache_manager.get(hash):
            return True
        return False

    def store_docs_to_db(self, file_paths: str):

        for file_path in file_paths:
            if self._doc_exists_in_cache(file_content=file_path):
                continue

            markdown = self._convert_to_markdown(file_path)
            file_content_hash = self._generate_hash(file_path)
            docs = self._chunk_mardown_doc(markdown)

            ids = []
            chunks = []
            metadatas = []
            for i, doc in enumerate(docs):
                headers = []
                page_content = doc.page_content
                for key in ["h1", "h2"]:
                    if key in doc.metadata:
                        headers.append(doc.metadata[key])
                if headers:
                    page_content = " > ".join(headers) + "\n\n" + doc.page_content

                ids.append(f"{file_content_hash}:{i}")
                chunks.append(page_content)
                metadatas.append(
                    {**doc.metadata, "hash": file_content_hash, "file_path": file_path}
                )

            vector_store.add(ids, chunks, metadatas)
            cache_manager.add(
                file_content_hash,
                {"file_path": file_path, "content": markdown, "chunks": chunks},
            )
