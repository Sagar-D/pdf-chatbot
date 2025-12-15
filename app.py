from helpers.document_manager import DocumentProcessor
from helpers.vectordb_manager import VectorDBManager
import hashlib


file_paths = ["/Users/sagard/Downloads/test_docling.pdf"]
doc_processor = DocumentProcessor()
markdowns = doc_processor.store_docs_to_db(file_paths=file_paths)

db_manager = VectorDBManager()

while True :

    query = input("User Query : ")

    docs = db_manager.fetch_similar_docs(query, 2)

    for doc in docs[0] :
        print("=="*40)
        print(doc)
        print("=="*40)



