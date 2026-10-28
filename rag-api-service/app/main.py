import logging
import os
import re
import unicodedata

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

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
    "CHROMA_DB_PATH", "temp/chroma_db"
)

CHROMA_S3_PREFIX = os.getenv(
    "CHROMA_S3_PREFIX", "processed/chroma_db"
)


# ============================================================
# 1. CATALOGO DE BOTS Y PDD INDEXADOS
# ============================================================
# Los document_id fueron verificados directamente en ChromaDB.
# Total: 12 PDD, 764 fragmentos.
# Cada consulta debe utilizar un documento identificado.

CATALOGO_BOTS = (
    {
        "nombre": "Bajas y Altas de Usuarios",
        "document_id":
            "15751 -PDD  RPA Bajas y Altas de Usuarios V2.0.3",
        "alias": (
            "bajas y altas de usuarios",
            "altas y bajas de usuarios",
            "bajas y altas",
            "altas y bajas"
        ),
    },
    {
        "nombre": "Carga de Datos de Autenticación",
        "document_id":
            "15818 -PDD  RPA Carga de Datos de Autenticación V1.0.1",
        "alias": (
            "carga de datos de autenticacion",
            "datos de autenticacion"
        ),
    },
    {
        "nombre": "Renovación de Pólizas",
        "document_id":
            "Formato 4.2 - Documento de Diseño - Renovacion de Polizas (Endosados Fase1 y Fase 2)V2.0",
        "alias": (
            "renovacion de polizas",
            "endosados fase 1",
            "endosados fase1"
        ),
    },
    {
        "nombre": "Creación de Depósito a Plazo PJ MO",
        "document_id":
            "Formato 4.2 - Documento funcional y de diseño - Creacion de deposito a plazo PJ MO V1.2",
        "alias": (
            "creacion de deposito a plazo",
            "deposito a plazo pj",
            "deposito a plazo"
        ),
    },
    {
        "nombre": "Cargo y Facturación de Garantías",
        "document_id":
            "Formato 4.2 - Documento funcional y de diseño - RPA Cargo y facturación de garantías - INN.011_PDD_V1.5",
        "alias": (
            "cargo y facturacion de garantias",
            "facturacion de garantias"
        ),
    },
    {
        "nombre": "Abono y Conciliación Cash Today",
        "document_id":
            "Formato 4.2- Abono y Conciliación Cash Today v1.4.8",
        "alias": (
            "abono y conciliacion cash today",
            "cash today"
        ),
    },
    {
        "nombre": "Generación de Cronogramas PN",
        "document_id":
            "Formato 4.2- Generación de Cronogramas PN V.1.0.2",
        "alias": (
            "generacion de cronogramas pn",
            "cronogramas pn",
            "generacion de cronogramas"
        ),
    },
    {
        "nombre": "Transferencias BCR",
        "document_id":
            "Formato 4.2- RPA TRANSFERENCIAS BCR V3.0.2",
        "alias": (
            "transferencias bcr",
            "transferencia bcr"
        ),
    },
    {
        "nombre": "Pago de Facturas",
        "document_id":
            "PDD_16029_RPA PAGO DE FACTURAS v1.3",
        "alias": (
            "pago de facturas",
            "pago facturas"
        ),
    },
    {
        "nombre": "Compra de Deuda - F2 Liberación CDD-LD",
        "document_id":
            "RPA Compra de deuda_F2_Liberación CDD-LD V1.0.1",
        "alias": (
            "compra de deuda f2",
            "compra de deuda flujo f2",
            "liberacion cdd ld",
            "liberacion cdd-ld"
        ),
    },
    {
        "nombre": "Compra de Deuda - F5 Respuesta de Prosegur",
        "document_id":
            "RPA Compra de deuda_F5_Respuesta de Prosegur V1.1.1",
        "alias": (
            "compra de deuda f5",
            "compra de deuda flujo f5",
            "respuesta de prosegur"
        ),
    },
)

# Versión histórica, utilizada solo si se solicita expresamente.
DOCUMENTO_CRONOGRAMAS_HISTORICO = (
    "Formato 4.2- Generación de Cronogramas PN V.1.0"
)


# ============================================================
# 2. NORMALIZACION Y DETECCION DEL BOT
# ============================================================

def normalizar(texto: str) -> str:
    """Normaliza tildes, mayúsculas y puntuación."""
    texto = unicodedata.normalize("NFKD", texto.lower())

    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )

    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def contiene_alias(texto_normalizado: str, alias: str) -> bool:
    """Comprueba un nombre completo, evitando coincidencias parciales."""
    patron = rf"(?:^| ){re.escape(normalizar(alias))}(?: |$)"

    return re.search(patron, texto_normalizado) is not None


def identificar_documento(pregunta: str):
    """
    Retorna:
      (document_id, None) cuando identifica un PDD.
      (None, mensaje) cuando debe solicitar aclaración.
    """

    texto = normalizar(pregunta)

    encontrados = [
        bot
        for bot in CATALOGO_BOTS
        if any(
            contiene_alias(texto, alias)
            for alias in bot["alias"]
        )
    ]

    # Reconocer expresiones como:
    # "F2 de Compra de Deuda" o "F5 de Compra de Deuda".
    if (
        contiene_alias(texto, "compra de deuda")
        or contiene_alias(texto, "compra deuda")
    ):
        for flujo in ("f2", "f5"):
            if re.search(rf"\b{flujo}\b", texto):
                candidato = next(
                    bot for bot in CATALOGO_BOTS
                    if bot["nombre"].startswith(
                        "Compra de Deuda - " + flujo.upper()
                    )
                )

                if candidato not in encontrados:
                    encontrados.append(candidato)

    # Más de un bot mencionado: evitar mezclar documentos.
    if len(encontrados) > 1:
        return None, (
            "Mencionaste varios bots o flujos. "
            "Indica solo uno y repite tu consulta "
            "para evitar mezclar procedimientos."
        )

    if encontrados:
        bot = encontrados[0]

        # Cronogramas PN: usar V1.0.2 por defecto.
        # Permitir V1.0 cuando se solicita expresamente.
        if bot["nombre"] == "Generación de Cronogramas PN":

            version_historica = bool(
                re.search(
                    r"\b(?:v\s*1\s+0|version\s+1\s+0)\b(?!\s+2)",
                    texto
                )
            )

            if version_historica:
                return DOCUMENTO_CRONOGRAMAS_HISTORICO, None

        return bot["document_id"], None

    # Compra de Deuda tiene varios PDD.
    if (
        contiene_alias(texto, "compra de deuda")
        or contiene_alias(texto, "compra deuda")
    ):
        return None, (
            "¿A qué flujo de Compra de Deuda te refieres: "
            "F2 (Liberación CDD-LD) o F5 (Respuesta de Prosegur)? "
            "Repite la consulta indicando el flujo."
        )

    # No existe un bot identificado.
    return None, (
        "¿A qué bot o proceso automatizado te refieres? "
        "Indica su nombre junto con la consulta; por ejemplo: "
        "«¿Qué sucede si el bot de Generación de Cronogramas PN "
        "no encuentra el archivo INPUT?»."
    )


def es_pregunta_catalogo(pregunta: str) -> bool:
    texto = normalizar(pregunta)

    expresiones = (
        "que bots puedes consultar",
        "cuales bots puedes consultar",
        "que robots puedes consultar",
        "cuales robots puedes consultar",
        "lista de bots",
        "que documentos tienes",
        "que procesos conoces",
    )

    return any(
        contiene_alias(texto, expresion)
        for expresion in expresiones
    )


# ============================================================
# 3. VALIDACION DE SOLICITUDES OPERATIVAS (P3)
# ============================================================

def es_solicitud_operativa(pregunta: str) -> bool:

    texto = normalizar(pregunta)

    menciona_robot = re.search(
        r"\b(robot|robots|bot|bots|rpa|automatizacion|proceso)\b",
        texto
    )

    menciona_proceso = any(
        contiene_alias(texto, alias)
        for bot in CATALOGO_BOTS
        for alias in bot["alias"]
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

    return bool(
        (menciona_robot or menciona_proceso)
        and solicita_accion
    )


# ============================================================
# 4. RESTAURACION DE CHROMADB DESDE S3
# ============================================================

def restore_chromadb_from_s3():

    logger.info("Restaurando ChromaDB desde S3...")

    s3_service = S3Service()

    s3_service.download_folder(
        CHROMA_S3_PREFIX,
        CHROMA_DB_PATH
    )

    logger.info(
        "ChromaDB restaurado correctamente desde S3."
    )


restore_chromadb_from_s3()

app = FastAPI(
    title="RPA LLM RAG API Service",
    version="1.2.0"
)

embedder = Embedder()
chroma_service = ChromaService()
llm_service = LLMService()


# ============================================================
# 5. ENDPOINTS DE SALUD
# ============================================================

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "rag-api-service",
        "version": "1.2.0"
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
            "model": os.getenv(
                "OPENAI_MODEL", "gpt-4.1-nano"
            ),
            "top_k": int(os.getenv("TOP_K", "5")),
        }

    except Exception:
        logger.exception("Error en health check")

        raise HTTPException(
            status_code=500,
            detail="El servicio no está saludable."
        )


# ============================================================
# 6. ENDPOINT PRINCIPAL RAG
# ============================================================

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):

    try:
        question = request.question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="La pregunta no puede estar vacía."
            )

        # P3: rechazar ejecución de robots.
        if es_solicitud_operativa(question):
            return AskResponse(
                question=question,
                answer=(
                    "No puedo ejecutar, detener ni reiniciar robots RPA. "
                    "Solo puedo orientar con procedimientos documentados. "
                    "Para ejecutar un bot, utiliza los canales "
                    "operativos autorizados."
                ),
                sources=[]
            )

        # Permitir consultar los procesos disponibles.
        if es_pregunta_catalogo(question):

            nombres = "\n".join(
                f"- {bot['nombre']}"
                for bot in CATALOGO_BOTS
            )

            return AskResponse(
                question=question,
                answer=(
                    "Puedo consultar estos procesos documentados:\n"
                    + nombres
                ),
                sources=[]
            )

        # Identificar el PDD correspondiente.
        document_id, aclaracion = identificar_documento(
            question
        )

        # Si no existe bot, pedir aclaración sin consultar OpenAI.
        if not document_id:
            return AskResponse(
                question=question,
                answer=aclaracion,
                sources=[]
            )

        # Generar embedding únicamente cuando hay un bot.
        top_k = int(os.getenv("TOP_K", "5"))

        logger.info(
            "Consulta RAG filtrada por document_id=%s",
            document_id
        )

        question_embedding = embedder.generate_embeddings(
            [question]
        )

        # Buscar exclusivamente en el PDD identificado.
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
                answer=(
                    "No encontré información suficiente "
                    "en el PDD seleccionado."
                ),
                sources=[]
            )

        context_parts = []
        sources = []

        for i, doc in enumerate(documents):

            metadata = (
                metadatas[i]
                if i < len(metadatas)
                else {}
            )

            # Comprobación adicional de aislamiento documental.
            if metadata.get("document_id") != document_id:
                logger.warning(
                    "Fragmento ignorado por document_id inesperado"
                )
                continue

            context_parts.append(
                f"Fuente: {metadata.get('source_file')}\n"
                f"Documento ID: {metadata.get('document_id')}\n"
                f"Chunk ID: {metadata.get('chunk_id')}\n"
                f"Contenido:\n{doc}"
            )

            sources.append(
                SourceChunk(
                    document_id=metadata.get("document_id"),
                    chunk_id=metadata.get("chunk_id"),
                    source_file=metadata.get("source_file"),
                    text=doc
                )
            )

        if not sources:
            return AskResponse(
                question=question,
                answer=(
                    "No encontré evidencia verificable "
                    "en el PDD seleccionado."
                ),
                sources=[]
            )

        context = "\n\n".join(context_parts)

        # P2 y P1 siguen utilizando las reglas del LLM existente.
        answer = llm_service.generate_answer(
            question=question,
            context=context
        )

        return AskResponse(
            question=question,
            answer=answer,
            sources=sources
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("Error procesando pregunta")

        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error procesando la pregunta."
        )
