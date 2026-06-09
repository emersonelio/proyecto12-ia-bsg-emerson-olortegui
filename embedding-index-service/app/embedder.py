from sentence_transformers import SentenceTransformer
import numpy as np


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        print(f"Cargando modelo de embeddings: {model_name}")
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: list[str]) -> np.ndarray:
        if not texts:
            raise ValueError("No hay textos para generar embeddings.")

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embeddings.astype("float32")