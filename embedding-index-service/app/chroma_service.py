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

        self.client = chromadb.PersistentClient(
            path=self.chroma_db_path
        )

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )

    def clear_collection(self):

        try:
            self.client.delete_collection(
                self.collection_name
            )
        except Exception:
            pass

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )

    def add_documents(
        self,
        ids,
        embeddings,
        documents,
        metadatas
    ):

        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas
        )

    def count(self):

        return self.collection.count()