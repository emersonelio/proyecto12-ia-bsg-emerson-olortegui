import chromadb


class ChromaService:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path="temp/chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="rpa_documents"
        )

    def clear_collection(self):

        try:
            self.client.delete_collection(
                "rpa_documents"
            )
        except:
            pass

        self.collection = self.client.get_or_create_collection(
            name="rpa_documents"
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