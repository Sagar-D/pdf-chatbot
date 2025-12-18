from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pdf_chatbot.documents.cache_manager import DocCacheManager
from pdf_chatbot.rag.vector_store import VectorStore
import hashlib
from typing import Union
from io import BytesIO

cache_manager = DocCacheManager()
vector_store = VectorStore.get_instance()
vector_store = VectorStore.get_instance()

doc_converter = DocumentConverter()


class DocumentProcessor:

    def _convert_to_markdown(self, file_content: bytes):
        pdf_file = BytesIO(file_content)
        pdf_file.name = "sample.pdf"
        doc = DocumentStream(name=pdf_file.name, stream=pdf_file)
        result = doc_converter.convert(source=doc)
        markdown = result.document.export_to_markdown()
        return markdown

    def _chunk_mardown_doc(self, markdown: str):
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2")]
        )
        chunks = splitter.split_text(markdown)
        return chunks

    def generate_hash(self, content: Union[bytes, str]):
        if type(content) == str:
            content = content.encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def _doc_exists_in_cache(self, file_content: bytes):
        hash = self.generate_hash(file_content)
        if cache_manager.get(hash):
            return True
        return False

    def store_docs_to_db(self, files: list[bytes]):

        file_hash_list = []

        for file in files:
            file_content_hash = self.generate_hash(file)
            file_hash_list.append(file_content_hash)

            if self._doc_exists_in_cache(file_content=file):
                continue

            markdown = self._convert_to_markdown(file)
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
                metadatas.append({**doc.metadata, "file_hash": file_content_hash})

            vector_store.add(ids, chunks, metadatas)
            cache_manager.add(
                file_content_hash,
                {"file": file, "content": markdown, "chunks": chunks},
            )
        return file_hash_list
