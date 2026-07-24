"""
load_documents.py — Script de carga independiente para la Tarea 2 (LangServe + Qdrant Cloud).

Se corre UNA VEZ (o cada vez que cambian las fuentes) para poblar Qdrant Cloud.
No vive dentro del servidor: el servidor (server.py) solo CONSULTA la colección
que este script deja creada.

Uso:
    python load_documents.py

Requiere en el .env: OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# Loaders específicos por tipo de archivo — cada formato necesita el suyo
from langchain_community.document_loaders import (
    TextLoader,
    Docx2txtLoader,
    PyPDFLoader,
)

 
load_dotenv(override=True)  # el .env de este proyecto siempre gana, aunque la sesión tenga otras variables cacheadas

# ============================================================================
# 1. CONSTANTES DEL PROYECTO
# ============================================================================
EMBED_MODEL = "text-embedding-3-large"
EMBED_DIMS = 256
COLLECTION = "tarea2_conduccion_multiformato"  # colección NUEVA, separada de la Tarea 1
DATA_DIR = Path(__file__).parent / "data"

assert os.getenv("OPENAI_API_KEY"), "Falta OPENAI_API_KEY en .env"
assert os.getenv("QDRANT_URL"), "Falta QDRANT_URL en .env"
assert os.getenv("QDRANT_API_KEY"), "Falta QDRANT_API_KEY en .env"


# ============================================================================
# 2. CARGA DE DOCUMENTOS — un loader distinto por cada tipo de archivo
# ============================================================================
def cargar_documentos() -> list[Document]:
    """
    Carga las 4 fuentes (mismo dominio: Libro para la Conducción en Chile, CONASET),
    cada una en su formato nativo. Cada Document lleva metadata de origen (archivo,
    capítulo) para poder citar la fuente después en las respuestas del RAG.
    """
    fuentes = [
        {
            "archivo": "cap1_siniestros_transito.md",
            "capitulo": "1 - Los siniestros de tránsito",
            "loader": lambda p: TextLoader(str(p), encoding="utf-8").load(),
        },
        {
            "archivo": "Capitulo2.txt",
            "capitulo": "2 - Los principios de la conducción",
            "loader": lambda p: TextLoader(str(p), encoding="utf-8").load(),
        },
        {
            "archivo": "Capitulo3.docx",
            "capitulo": "3 - Convivencia Vial",
            "loader": lambda p: Docx2txtLoader(str(p)).load(),
        },
        {
            "archivo": "cap4.pdf",  # PDF nativo, texto real extraíble (no escaneado)
            "capitulo": "4 - Las personas en el tránsito",
            "loader": lambda p: PyPDFLoader(str(p)).load(),
        },
    ]

    documentos = []
    for f in fuentes:
        ruta = DATA_DIR / f["archivo"]
        if not ruta.exists():
            print(f"⚠️  Saltando {f['archivo']} (no encontrado en {DATA_DIR})")
            continue
        docs_cargados = f["loader"](ruta)
        # PyPDFLoader devuelve 1 Document por página; el resto, 1 por archivo.
        # Unificamos metadata para todos, sea cual sea el loader de origen.
        for d in docs_cargados:
            d.metadata.update({
                "fuente": "Libro para la Conducción en Chile - CONASET (2024)",
                "capitulo": f["capitulo"],
                "archivo": f["archivo"],
                "tipo_archivo": ruta.suffix.lstrip("."),
            })
        documentos.extend(docs_cargados)
        print(f"✓ Cargado {f['archivo']} ({ruta.suffix}) · {len(docs_cargados)} documento(s)")

    return documentos


# ============================================================================
# 3. CHUNKING JUSTIFICADO
#    Mismo criterio validado en la Tarea 1: split por estructura (headers)
#    donde el documento lo permite (.md/.txt con "##"), + recursive dentro de
#    cada sección. Para el PDF (que viene paginado, sin headers markdown) se
#    aplica directamente recursive sobre cada página.
#    Config elegida: chunk_size=800, overlap=120 — evita cortar unidades
#    completas a la mitad (validado empíricamente en la Tarea 1 con el caso
#    de los "4 principios del Sistema Seguro").
# ============================================================================
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def chunkear(documentos: list[Document]) -> list[Document]:
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("##", "seccion")], strip_headers=False
    )
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc in documentos:
        tiene_headers = "##" in doc.page_content
        if tiene_headers:
            # Por estructura primero, luego recursive dentro de cada sección
            secciones = md_splitter.split_text(doc.page_content)
            for sec in secciones:
                sub_docs = recursive_splitter.create_documents(
                    [sec.page_content],
                    metadatas=[{**doc.metadata, **sec.metadata}],
                )
                chunks.extend(sub_docs)
        else:
            # Sin headers (ej. páginas de PDF o .docx sin marcado) -> recursive directo
            sub_docs = recursive_splitter.create_documents(
                [doc.page_content], metadatas=[doc.metadata]
            )
            chunks.extend(sub_docs)

    return chunks


# ============================================================================
# 4. INDEXAR EN QDRANT CLOUD
# ============================================================================
def indexar(chunks: list[Document]) -> None:
    client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL, dimensions=EMBED_DIMS)

    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=EMBED_DIMS, distance=Distance.COSINE),
    )

    vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION, embedding=embeddings)
    vector_store.add_documents(chunks)

    info = client.get_collection(COLLECTION)
    print(f"\n✅ Índice listo · {info.points_count} vectores en Qdrant/{COLLECTION} "
          f"(COSINE, {EMBED_DIMS}d)")

    ejemplo = client.scroll(collection_name=COLLECTION, limit=1, with_payload=True)[0][0]
    print("\n--- Registro de ejemplo ---")
    print("id:", ejemplo.id)
    print("payload (metadata):", {k: v for k, v in ejemplo.payload.items() if k != "page_content"})


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print(f"Cargando documentos desde: {DATA_DIR}\n")
    documentos = cargar_documentos()
    print(f"\nTotal documentos cargados: {len(documentos)}")

    chunks = chunkear(documentos)
    print(f"Total chunks generados: {len(chunks)} (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})\n")

    indexar(chunks)
