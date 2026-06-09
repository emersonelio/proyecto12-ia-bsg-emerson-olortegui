import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from app.embedder import Embedder
from app.chroma_service import ChromaService
from app.llm_service import LLMService
from app.schemas import AskRequest, AskResponse, SourceChunk


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="RPA LLM RAG API Service",
    version="1.0.0"
)

embedder = Embedder()
chroma_service = ChromaService()
llm_service = LLMService()


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "rag-api-service"
    }


@app.get("/health")
def health():
    try:
        return {
            "status": "healthy",
            "service": "rag-api-service",
            "vector_store": "chromadb",
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

        top_k = int(os.getenv("TOP_K", "5"))

        logger.info(f"Pregunta recibida: {question}")

        question_embedding = embedder.generate_embeddings([question])

        results = chroma_service.search(
            query_embedding=question_embedding,
            top_k=top_k
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        if not documents:
            return AskResponse(
                question=question,
                answer="No encontré información suficiente en los documentos indexados.",
                sources=[]
            )

        context_parts = []
        sources = []

        for i, doc in enumerate(documents):
            metadata = metadatas[i]

            context_parts.append(
                f"""
Fuente: {metadata.get("source_file")}
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