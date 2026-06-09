import re
from langchain_text_splitters import RecursiveCharacterTextSplitter


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MIN_CHUNK_LENGTH = 250


def clean_extracted_text(text: str):
    # Normalizar saltos de línea
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Quitar encabezados repetidos comunes en PDD
    patterns_to_remove = [
        r"COEH\s*\nGerencia de Arquitectura y Datos\s*\nVicepresidencia de Tecnología y Operaciones",
        r"Documento de Diseño\s*\n\s*\d+/\d+",
        r"COE - RPA\s*\nSubgerencia de Operaciones\s*\nVicepresidencia de Operaciones y Tecnología",
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Quitar páginas tipo 3/85 cuando aparecen solas
    text = re.sub(r"\n\s*\d+/\d+\s*\n", "\n", text)

    # Quitar índice inicial si existe
    text = re.sub(
        r"Contenido\s+.*?(?=1\.\s*Objetivo del proceso)",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Reducir saltos de línea excesivos
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    return text.strip()


def create_chunks(text: str):
    cleaned_text = clean_extracted_text(text)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    raw_chunks = splitter.split_text(cleaned_text)

    chunks = []

    for chunk in raw_chunks:
        chunk = chunk.strip()

        if len(chunk) >= MIN_CHUNK_LENGTH:
            chunks.append(chunk)

    return chunks