import os
from pathlib import Path

from app.extractor import extract_text_from_pdf
from app.cleaner import clean_text
from app.metadata import build_metadata

from app.s3_service import (
    list_pdf_files,
    download_pdf,
    upload_text,
    upload_metadata
)


def process_documents():
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    pdf_files = list_pdf_files()

    print(f"PDFs encontrados: {len(pdf_files)}")

    for s3_key in pdf_files:
        file_name = Path(s3_key).stem
        local_path = os.path.join(temp_dir, Path(s3_key).name)

        print(f"Procesando: {s3_key}")

        download_pdf(s3_key, local_path)

        raw_text, total_pages = extract_text_from_pdf(local_path)
        cleaned_text = clean_text(raw_text)

        s3_text_key = upload_text(file_name, cleaned_text)
        s3_metadata_key = f"processed/metadata/{file_name}.json"

        metadata_result = build_metadata(
            file_path=local_path,
            total_pages=total_pages,
            s3_raw_key=s3_key,
            s3_text_key=s3_text_key,
            s3_metadata_key=s3_metadata_key,
            text_characters=len(cleaned_text)
        )

        upload_metadata(file_name, metadata_result)

        print(f"OK -> {file_name}")

    print("Proceso finalizado")


if __name__ == "__main__":
    process_documents()