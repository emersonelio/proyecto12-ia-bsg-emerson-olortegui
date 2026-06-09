import os
from dotenv import load_dotenv

from app.embedder import Embedder
from app.s3_service import S3Service
from app.chroma_service import ChromaService


def ensure_temp_folder():

    os.makedirs("temp", exist_ok=True)
    os.makedirs("temp/chroma_db", exist_ok=True)


def main():

    load_dotenv()

    ensure_temp_folder()

    s3_service = S3Service()
    embedder = Embedder()
    chroma_service = ChromaService()

    print("Limpiando colección anterior...")
    chroma_service.clear_collection()

    print("Buscando archivos de chunks en S3...")

    chunk_files = s3_service.list_chunk_files()

    if not chunk_files:
        print("No se encontraron archivos.")
        return

    all_chunks = []

    for chunk_file in chunk_files:

        print(f"Leyendo chunks: {chunk_file}")

        chunks = s3_service.download_json(chunk_file)

        for chunk in chunks:

            text = chunk.get("chunk_text", "").strip()

            if text:
                all_chunks.append(chunk)

    print(f"Total chunks válidos encontrados: {len(all_chunks)}")

    if not all_chunks:
        return

    texts = []

    ids = []

    metadatas = []

    for chunk in all_chunks:

        texts.append(
            chunk["chunk_text"]
        )

        ids.append(
            f"{chunk['document_id']}_{chunk['chunk_id']}"
        )

        metadatas.append({
             "document_id": chunk.get("document_id"),
             "chunk_id": chunk.get("chunk_id"),
             "source_file": chunk.get("source_file"),
                "s3_text_key": chunk.get("s3_text_key"),
             "s3_metadata_key": chunk.get("s3_metadata_key")
        })

    print("Generando embeddings...")

    embeddings = embedder.generate_embeddings(
        texts
    )

    print(
        f"Dimensión embeddings: {embeddings.shape}"
    )

    print("Insertando en ChromaDB...")

    chroma_service.add_documents(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(
        f"Total registros en ChromaDB: {chroma_service.count()}"
    )

    print("Proceso finalizado correctamente.")


if __name__ == "__main__":
    main()