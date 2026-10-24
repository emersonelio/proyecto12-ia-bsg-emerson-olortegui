
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

    def search(self, query_embedding, top_k=5, document_id=None):

        # P1 - Exigir un documento específico
        if not document_id or not document_id.strip():
            raise ValueError(
                "Debe especificarse un document_id para la búsqueda."
            )

        # P1 - Búsqueda semántica filtrada por documento
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k,
            where={
                "document_id": document_id.strip()
            }
        )

        return results
