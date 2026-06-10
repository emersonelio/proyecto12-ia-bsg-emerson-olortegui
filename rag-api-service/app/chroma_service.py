import os
import chromadb


class ChromaService:

    def __init__(self):

        self.chroma_db_path = os.getenv(
            "CHROMA_DB_PATH",
            "temp/chroma_db"
        )

        self.collection_name = os.getenv(
            "CHROMA_COLLECTION",
            "rpa_documents"
        )

        print(f"Conectando a ChromaDB: {self.chroma_db_path}")

        self.client = chromadb.PersistentClient(
            path=self.chroma_db_path
        )

        self.collection = self.client.get_collection(
            name=self.collection_name
        )

    def search(self, query_embedding, top_k=5):

        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k
        )

        return results