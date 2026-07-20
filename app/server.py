"""FastAPI service that exposes a RAG Retriever Agent (LangGraph) over an external
Qdrant Cloud collection, as an HTTP API.

The collection must already be populated — run `load_documents.py` first (a separate,
independent script; it does NOT run inside this server).

The agent has ONE tool: `buscar_en_documento`, which does similarity search against
Qdrant. The LLM decides when to call it (or not — e.g. for greetings) and always
answers grounded only in what the tool returns, citing the section/chapter.
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langgraph.prebuilt import create_react_agent

load_dotenv()  # reads OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY from .env

logger = logging.getLogger("rag-agent")

# --- Constantes (deben calzar con las usadas en load_documents.py) -----------
EMBED_MODEL = "text-embedding-3-large"
EMBED_DIMS = 256
COLLECTION = "tarea2_conduccion_multiformato"
GEN_MODEL = "gpt-5.4-mini"
TOP_K = 4

for var in ("OPENAI_API_KEY", "QDRANT_URL", "QDRANT_API_KEY"):
    if not os.getenv(var):
        raise RuntimeError(f"Falta la variable de entorno {var} (revisa tu .env o los secrets de fly.io)")

# --- Observabilidad con Langfuse (opcional y degradante) ----------------------
# Si faltan las claves, el servidor sigue funcionando igual, solo sin trazas.
_LANGFUSE_ACTIVO = bool(os.getenv("LANGFUSE_PUBLIC_KEY")) and bool(os.getenv("LANGFUSE_SECRET_KEY"))
_langfuse_handler = None

if _LANGFUSE_ACTIVO:
    try:
        from langfuse import get_client
        from langfuse.langchain import CallbackHandler

        _langfuse_client = get_client()
        if _langfuse_client.auth_check():
            _langfuse_handler = CallbackHandler()
            print(f"✅ Langfuse activo → {os.getenv('LANGFUSE_BASE_URL')}")
        else:
            print("⚠️  Las claves de Langfuse no pasaron auth_check() — continuando sin trazas.")
    except Exception as e:
        print(f"⚠️  No se pudo inicializar Langfuse: {e!r} — continuando sin trazas.")
else:
    print("ℹ️  Sin claves de Langfuse en .env — continuando sin trazas.")

# --- Vector store (conexión a la colección YA poblada) -----------------------
_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
_embeddings = OpenAIEmbeddings(model=EMBED_MODEL, dimensions=EMBED_DIMS)
_vector_store = QdrantVectorStore(client=_client, collection_name=COLLECTION, embedding=_embeddings)


# --- Tool del agente: retriever sobre Qdrant ---------------------------------
@tool
def buscar_en_documento(pregunta: str) -> str:
    """Busca pasajes relevantes en el 'Libro para la Conducción en Chile' (CONASET)
    para responder la pregunta del usuario. Devuelve los pasajes encontrados con
    su capítulo/sección de origen, para poder citarlos."""
    docs = _vector_store.similarity_search(pregunta, k=TOP_K)
    if not docs:
        return "No se encontraron pasajes relevantes para esta pregunta."
    return "\n\n".join(
        f"[Capítulo: {d.metadata.get('capitulo', '?')}] {d.page_content}" for d in docs
    )


SYSTEM_PROMPT = (
    "Eres un asistente que responde preguntas sobre el 'Libro para la Conducción "
    "en Chile' (CONASET). Usa SIEMPRE la herramienta 'buscar_en_documento' antes de "
    "responder cualquier pregunta sobre el contenido del libro. Responde SOLO con lo "
    "que la herramienta devuelva, citando el capítulo entre [corchetes]. Si la "
    "herramienta no trae información suficiente, responde exactamente: "
    "'No tengo información suficiente para responder esa pregunta.' No inventes datos."
)

_agent = create_react_agent(
    model=ChatOpenAI(model=GEN_MODEL, reasoning_effort="none"),
    tools=[buscar_en_documento],
    prompt=SYSTEM_PROMPT,
)


def responder(pregunta: str) -> str:
    """Invoca el agente y devuelve solo el texto de la última respuesta."""
    config = {"callbacks": [_langfuse_handler]} if _langfuse_handler else {}
    resultado = _agent.invoke({"messages": [{"role": "user", "content": pregunta}]}, config=config)
    if _LANGFUSE_ACTIVO and "_langfuse_client" in globals():
        _langfuse_client.flush()  # fuerza el envío inmediato de la traza (útil en pruebas)
    return resultado["messages"][-1].content


# --- Request / response models ------------------------------------------------
class PreguntaRequest(BaseModel):
    pregunta: str = Field(..., description="Pregunta sobre el Libro para la Conducción en Chile.")


class RespuestaResponse(BaseModel):
    respuesta: str


# --- FastAPI app --------------------------------------------------------------
app = FastAPI(
    title="RAG Retriever Agent — Libro para la Conducción en Chile",
    version="1.0",
    description=(
        "Agente Retriever (LangGraph) sobre una colección de Qdrant Cloud ya poblada. "
        "Prueba interactiva en /docs."
    ),
)


@app.get("/")
def health():
    """Liveness check — usado por fly.io y balanceadores de carga."""
    return {"status": "ok", "service": "rag-retriever-agent", "docs": "/docs"}


@app.post("/ask", response_model=RespuestaResponse)
async def ask(request: PreguntaRequest):
    """Responde una pregunta usando el Agente Retriever sobre Qdrant Cloud."""
    try:
        respuesta = responder(request.pregunta)
    except Exception:
        logger.exception("Fallo al responder la pregunta")
        raise HTTPException(status_code=502, detail="Fallo interno; revisa los logs del servidor.")
    return RespuestaResponse(respuesta=respuesta)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))