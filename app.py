from helpers.document_manager import DocumentProcessor
from helpers.retriever_manager import Retriever

file_paths = [
    "/Users/sagard/Downloads/test_docling.pdf",
    "/Users/sagard/Downloads/iphone17.pdf",
    "/Users/sagard/Downloads/india_press_note.pdf"
]
doc_processor = DocumentProcessor()
doc_processor.store_docs_to_db(file_paths=file_paths)

retriever = Retriever(type="hybrid")

while True:

    query = input("User Query : ")
    docs = retriever.query_docs(query=query)
    for doc in docs[:5]:
        print("==" * 40)
        print(doc)
        print("==" * 40)
