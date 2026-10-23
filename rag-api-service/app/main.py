import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import re
import unicodedata

from app.embedder import Embedder
from app.s3_service import S3Service
from app.chroma_service import ChromaService
from app.llm_service import LLMService
from app.schemas import AskRequest, AskResponse, SourceChunk


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

CHROMA_DB_PATH = os.getenv(
    "CHROMA_DB_PATH",
    "temp/chroma_db"
)

CHROMA_S3_PREFIX = os.getenv(
    "CHROMA_S3_PREFIX",
    "processed/chroma_db"
)



def restore_chromadb_from_s3():
    logger.info("Restaurando ChromaDB desde S3...")

    s3_service = S3Service()

    s3_service.download_folder(
        CHROMA_S3_PREFIX,
        CHROMA_DB_PATH
    )

    logger.info("ChromaDB restaurado correctamente desde S3.")



def es_solicitud_operativa(pregunta: str) -> bool:
    texto = unicodedata.normalize("NFKD", pregunta.lower())
    texto = "".join(
        c for c in texto if not unicodedata.combining(c)
    )
    texto = texto.strip(" ¿?¡!.,\n\t")

    menciona_robot = re.search(
        r"\b(robot|robots|bot|bots|rpa)\b",
        texto
    )

    solicita_accion = re.search(
        r"^(por favor\s+)?"
        r"(ejecuta|inicia|lanza|arranca|reinicia|deten|detiene)\b"
        r"|^(puedes|podrias)\s+"
        r"(ejecutar|iniciar|lanzar|reiniciar|detener)\b"
        r"|^(quiero|necesito)\s+que\s+"
        r"(ejecutes|inicies|lances|reinicies|detengas)\b",
        texto
    )

    return bool(menciona_robot and solicita_accion)


restore_chromadb_from_s3()

app = FastAPI(
    title="RPA LLM RAG API Service",
    version="1.1.0"
)

embedder = Embedder()
chroma_service = ChromaService()
llm_service = LLMService()


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "rag-api-service",
        "version": "1.1.0"
    }


@app.get("/health")
def health():
    try:
        return {
            "status": "healthy",
            "service": "rag-api-service",
            "vector_store": "chromadb",
            "chroma_db_path": CHROMA_DB_PATH,
            "chroma_s3_prefix": CHROMA_S3_PREFIX,
            "documents_indexed": chroma_service.collection.count(),
            "llm_provider": "openai",
            "model": os.getenv("OPENAI_MODEL", "gpt-4.1-nano"),
            "top_k": int(os.getenv("TOP_K", "5"))
        }

    except Exception as error:
        logger.error(f"Error en health check: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail="El servicio no está saludable."
        )


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        question = request.question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="La pregunta no puede estar vacía."
            )

        if es_solicitud_operativa(question):
            logger.info("Solicitud operativa fuera de alcance rechazada.")
            return AskResponse(
                question=question,
                answer=(
                    "No puedo ejecutar, detener ni reiniciar robots RPA. "
                    "Mi función es consultar procedimientos documentados "
                    "en los PDD autorizados. "
                    "Para solicitar una ejecución, comunícate con el "
                    "equipo RPA o utiliza el canal operativo autorizado."
                ),
                sources=[]

            )
        top_k = int(os.getenv("TOP_K", "5"))

        logger.info(f"Pregunta recibida: {question}")

        question_embedding = embedder.generate_embeddings(
            [question]
        )        
        # P1 - Seleccionar el PDD para la PoC     
        document_id = os.getenv(
            "PDD_DOCUMENT_ID",
            "Formato 4.2- Generación de Cronogramas PN V.1.0.2"
        ).strip()

        # P1 - Buscar únicamente en el documento seleccionado
        results = chroma_service.search(
            query_embedding=question_embedding,
            top_k=top_k,
            document_id=document_id
        )
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            return AskResponse(
                question=question,
                answer="No encontré información suficiente en los documentos indexados.",
                sources=[]
            )

        context_parts = []
        sources = []

        for i, doc in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}

            context_parts.append(
                f"""
Fuente: {metadata.get("source_file")}
Documento ID: {metadata.get("document_id")}
Chunk ID: {metadata.get("chunk_id")}
Contenido:
{doc}
"""
            )

            sources.append(
                SourceChunk(
                    document_id=metadata.get("document_id"),
                    chunk_id=metadata.get("chunk_id"),
                    source_file=metadata.get("source_file"),
                    text=doc
                )
            )

        context = "\n\n".join(context_parts)

        answer = llm_service.generate_answer(
            question=question,
            context=context
        )

        logger.info("Respuesta generada correctamente.")

        return AskResponse(
            question=question,
            answer=answer,
            sources=sources
        )

    except HTTPException:
        raise

    except Exception as error:
        logger.error(f"Error procesando pregunta: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error procesando la pregunta."
        )