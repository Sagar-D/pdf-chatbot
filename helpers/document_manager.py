from docling.document_converter import DocumentConverter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from helpers.doc_cache_manager import DocCacheManager
from helpers.vectordb_manager import VectorDBManager
import hashlib

cache_manager = DocCacheManager()
db_manager = VectorDBManager()

class DocumentProcessor:

    def __init__(self):
        pass

    def convert_to_markdown(self, file_path:str):
        doc_converter = DocumentConverter()
        result = doc_converter.convert(source=file_path)
        markdown = result.document.export_to_markdown()
        return markdown

    def chunk_mardown_doc(self, markdown: str):
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "Header 1"), ("##", "Header 2")])
        chunks = splitter.split_text(markdown)
        return chunks

    def _generate_hash(self, content:str) :
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def doc_exists_in_cache(self, markdown: str):
        hash = self._generate_hash(markdown)
        if cache_manager.get(hash):
            return True
        return False
    
    def store_docs_to_db(self, file_paths:str) :
        
        for file_path in file_paths :
            markdown = self.convert_to_markdown(file_path)
            markdown_hash = self._generate_hash(markdown)
            if self.doc_exists_in_cache(markdown=markdown) :
                continue
            
            docs = self.chunk_mardown_doc(markdown)
            ids = []
            chunks = []
            metadatas = []
            for i in range(len(docs)) :
                ids.append(f"{markdown_hash}:{i}")
                chunks.append(docs[i].page_content)
                metadatas.append({
                    "hash": markdown_hash,
                    "file_path": file_path
                })
            
            db_manager.add(ids, chunks, metadatas)
            cache_manager.add(markdown_hash, {"file_path": file_path})
            
