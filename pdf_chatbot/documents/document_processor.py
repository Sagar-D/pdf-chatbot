from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pdf_chatbot.rag.vector_store import VectorStore
from langchain_core.documents import Document
import hashlib
from typing import Union
from io import BytesIO

vector_store: VectorStore = VectorStore.get_instance()
doc_converter = DocumentConverter()


def _convert_to_markdown(file_content: bytes) -> str:
    pdf_file = BytesIO(file_content)
    pdf_file.name = "sample.pdf"
    doc = DocumentStream(name=pdf_file.name, stream=pdf_file)
    result = doc_converter.convert(source=doc)
    markdown = result.document.export_to_markdown()
    return markdown


def _chunk_mardown_doc(markdown: str) -> list[Document]:
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2")]
    )
    chunks = splitter.split_text(markdown)
    for chunk in chunks:
        headers = [chunk.metadata[key] for key in ["h1", "h2"] if key in chunk.metadata]
        if headers:
            chunk.page_content = (" > ".join(headers)) + "\n\n" + chunk.page_content
    return chunks


def generate_hash(content: Union[bytes, str]) -> str:
    if type(content) == str:
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def save_user_documents(files: list[bytes], user_id: int) -> list[str]:
    document_hash_list = []
    for file in files:
        document_hash_id = generate_hash(content=file)
        document_hash_list.append(document_hash_id)

        document_already_processed = vector_store.document_exists(
            metadata_filter={
                "$and": [{"user_id": user_id}, {"document_hash_id": document_hash_id}]
            }
        )
        if document_already_processed:
            continue

        markdown = _convert_to_markdown(file)
        chunks: list[Document] = _chunk_mardown_doc(markdown)

        ids, page_contents, metadatas = [], [], []
        for i, chunk in enumerate(chunks):
            ids.append(f"{document_hash_id}:{i}")
            page_contents.append(chunk.page_content)
            metadatas.append(
                {
                    **chunk.metadata,
                    "user_id": user_id,
                    "document_hash_id": document_hash_id,
                    "chunk_id": f"{document_hash_id}:{i}",
                    "source_file": "NA",  # To be updated when we start saving user files on server
                    "chunk_content": chunk.page_content,
                }
            )
        vector_store.add(ids, page_contents, metadatas)
    return document_hash_list
