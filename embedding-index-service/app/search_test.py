from dotenv import load_dotenv

from embedder import Embedder
from chroma_service import ChromaService


def main():
    load_dotenv()

    pregunta = "no se ha identificado el archivo INPUT en la ruta compartida"
    print(f"Pregunta: {pregunta}")

    embedder = Embedder()
    chroma_service = ChromaService()

    query_embedding = embedder.generate_embeddings([pregunta])

    results = chroma_service.collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=3
    )

    print("\nResultados encontrados:\n")

    for i in range(len(results["documents"][0])):
        print("=" * 80)
        print(f"Resultado {i + 1}")
        print(f"Distancia: {results['distances'][0][i]}")
        print(f"Metadata: {results['metadatas'][0][i]}")
        print("\nTexto:")
        print(results["documents"][0][i])


if __name__ == "__main__":
    main()