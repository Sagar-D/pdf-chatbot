import chromadb


DEFAULT_COLLECTION_NAME = "pdf-chatbot-collection"
db = chromadb.PersistentClient()

class VectorDBManager:

    def __init__(self, collection_name: str = ""):
        if collection_name and collection_name.strip() != "":
            self.collection_name = collection_name.strip()
        else:
            self.collection_name = DEFAULT_COLLECTION_NAME

        self.collection = db.get_or_create_collection(self.collection_name)

    def add(self, ids, chunks, metadatas):
        self.collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    
    def fetch_similar_docs(self, query:str, limit:int = 20) :
        results = self.collection.query(query_texts=[query], n_results=limit)
        return results["documents"]

