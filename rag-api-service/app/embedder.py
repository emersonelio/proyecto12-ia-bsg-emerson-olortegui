from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        print(f"Cargando modelo de embeddings: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)

    def generate_embeddings(self, texts):
        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )