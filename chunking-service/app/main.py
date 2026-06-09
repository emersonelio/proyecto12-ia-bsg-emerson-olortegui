from app.chunker import create_chunks, CHUNK_SIZE, CHUNK_OVERLAP

from app.s3_service import (
    list_metadata_files,
    read_json,
    read_text,
    upload_chunks
)


def process_documents():
    metadata_files = list_metadata_files()

    print(f"Metadata encontrados: {len(metadata_files)}")

    for metadata_key in metadata_files:
        metadata = read_json(metadata_key)

        document_id = metadata["document_id"]
        s3_text_key = metadata["s3_text_key"]
        source_file = metadata["file_name"]

        print(f"Procesando: {document_id}")

        text = read_text(s3_text_key)
        raw_chunks = create_chunks(text)

        chunks = []

        for index, chunk_text in enumerate(raw_chunks, start=1):
            chunks.append({
                "document_id": document_id,
                "chunk_id": index,
                "chunk_text": chunk_text,
                "chunk_size": CHUNK_SIZE,
                "chunk_overlap": CHUNK_OVERLAP,
                "chunking_strategy": "semantic_recursive",
                "source_file": source_file,
                "s3_text_key": s3_text_key,
                "s3_metadata_key": metadata_key
            })

        s3_chunks_key = upload_chunks(document_id, chunks)

        print(f"OK -> {document_id}")
        print(f"Chunks generados: {len(chunks)}")
        print(f"S3 output: {s3_chunks_key}")

    print("Proceso finalizado")


if __name__ == "__main__":
    process_documents()