from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from pdf_chatbot.rag.vector_store import VectorStore
from pdf_chatbot.errors.document_error import (
    DocumentConversionError,
    DocumentChunkingError,
    InvalidDocumentError,
)
from pdf_chatbot import config
import hashlib
from typing import Union
from io import BytesIO
import asyncio

vector_store: VectorStore = VectorStore.get_instance()
doc_converter = DocumentConverter()


def _convert_to_markdown(file_content: bytes) -> str:
    try:
        pdf_file = BytesIO(file_content)
        pdf_file.name = "sample.pdf"
        doc = DocumentStream(name=pdf_file.name, stream=pdf_file)
        result = doc_converter.convert(source=doc)
        markdown = result.document.export_to_markdown()
    except Exception:
        raise DocumentConversionError(
            "Failed to extract PDF content for the files passed. Please check the file uploaded"
        )
    return markdown


def _chunk_mardown_doc(markdown: str) -> list[Document]:
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2")]
    )
    try:
        chunks = splitter.split_text(markdown)
    except Exception:
        raise DocumentChunkingError(
            "Failed to chunk the document content. Please check the file uploaded"
        )
    for chunk in chunks:
        headers = [chunk.metadata[key] for key in ["h1", "h2"] if key in chunk.metadata]
        if headers:
            chunk.page_content = (" > ".join(headers)) + "\n\n" + chunk.page_content
    return chunks


def generate_hash(content: Union[bytes, str]) -> str:
    if type(content) == str:
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


async def _process_individual_document(file: bytes, user_id: int) -> str:

    document_hash_id = generate_hash(content=file)

    def document_alread_processed():
        return vector_store.document_exists(
            metadata_filter={
                "$and": [
                    {"user_id": user_id},
                    {"document_hash_id": document_hash_id},
                ]
            }
        )

    if await asyncio.to_thread(document_alread_processed):
        return document_hash_id

    markdown = await asyncio.to_thread(_convert_to_markdown, file)
    chunks: list[Document] = await asyncio.to_thread(_chunk_mardown_doc, markdown)

    ids, page_contents, metadatas = [], [], []
    for i, chunk in enumerate(chunks):
        ids.append(f"{user_id}:{document_hash_id}:{i}:")
        page_contents.append(chunk.page_content)
        metadatas.append(
            {
                **chunk.metadata,
                "user_id": user_id,
                "document_hash_id": document_hash_id,
                "chunk_id": f"{user_id}:{document_hash_id}:{i}",
                "source_file": "NA",  # To be updated when we start saving user files on server
                "chunk_content": chunk.page_content,
            }
        )
    await asyncio.to_thread(vector_store.add, ids, page_contents, metadatas)
    return document_hash_id


async def save_user_documents(files: list[bytes], user_id: int) -> list[str]:

    document_ingestion_semaphore = asyncio.Semaphore(2)

    async def guarded_doument_ingestion_process(file):
        async with document_ingestion_semaphore:
            return await _process_individual_document(file, user_id)

    document_hash_list = await asyncio.gather(
        *(guarded_doument_ingestion_process(file) for file in files)
    )
    return document_hash_list


def verify_user_documents(files: list[bytes]):

    if len(files) > 3:
        raise InvalidDocumentError(
            "Too many files uploaded. Maximum of 3 files allowed."
        )
    for file in files:
        if len(file) > (config.MAX_FILE_SIZE_MB * 1024 * 1024):
            raise InvalidDocumentError(
                f"File exceeds maximum allowed size ({config.MAX_FILE_SIZE_MB} MB)"
            )
