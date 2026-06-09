from datetime import datetime
from pathlib import Path


def build_metadata(
    file_path: str,
    total_pages: int,
    s3_raw_key: str,
    s3_text_key: str,
    s3_metadata_key: str,
    text_characters: int
):
    file = Path(file_path)
    document_id = file.stem

    return {
        "document_id": document_id,
        "file_name": file.name,
        "file_extension": file.suffix.lower(),
        "total_pages": total_pages,
        "processed_at": datetime.now().isoformat(),
        "source": "etl-metadata-service",
        "s3_raw_key": s3_raw_key,
        "s3_text_key": s3_text_key,
        "s3_metadata_key": s3_metadata_key,
        "text_characters": text_characters
    }