# tarea-rag-deployado

Agente Retriever (RAG) sobre **Qdrant Cloud**, servido con **FastAPI** y desplegado en **fly.io**.
Tarea RAG (3 semanas) — Diplomado en IA Generativa.

Documento fuente: *Libro para la Conducción en Chile* (CONASET, 2024) — 3 fuentes en formatos distintos (`.txt`/`.md`, `.pdf`, `.docx`), mismo dominio temático.

## Arquitectura

```
load_documents.py  →  Qdrant Cloud (colección: tarea2_conduccion_multiformato)
                              ↑
                    app/server.py (FastAPI)  →  Agente Retriever (LangGraph)
                              ↑
                         POST /ask {"pregunta": "..."}
```

`load_documents.py` se corre **una sola vez** (o cuando cambian las fuentes) para poblar Qdrant. El servidor (`app/server.py`) **solo consulta** esa colección — nunca la modifica.

## Requisitos previos

Antes de clonar y correr este proyecto, necesitas tener instalado:

- **Python 3.11 o superior**
- **Poetry** (gestor de dependencias) — si no lo tienes:
  ```bash
  pip install poetry
  poetry --version   # confirma que quedó instalado
  ```
- **Docker Desktop** (solo si vas a correr o construir la imagen localmente)
- **flyctl** (solo si vas a desplegar en fly.io) — instrucciones en https://fly.io/docs/flyctl/install/

## Setup local

```bash
cp .env.example .env   # completa OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY
poetry install --with dev   # --with dev instala también lo que necesita load_documents.py
```

## 1. Poblar Qdrant (una vez)

```bash
poetry run python load_documents.py
```

## 2. Correr el servidor localmente

```bash
poetry run uvicorn app.server:app --reload --port 8000
```

Abre **http://localhost:8000/docs** (Swagger — el "playground" interactivo) y prueba `POST /ask`:
```json
{ "pregunta": "¿Cuáles son los 4 principios del Sistema Seguro?" }
```

## 3. Correr en Docker

```bash
docker build . -t tarea-rag-deployado
docker run --env-file .env -p 8080:8080 tarea-rag-deployado
```
Abre **http://localhost:8080/docs**.

## 4. Desplegar en fly.io

```bash
fly launch            # nombre único, genera tu propio fly.toml
fly secrets set OPENAI_API_KEY=... QDRANT_URL=... QDRANT_API_KEY=...
fly deploy
```

## Chunking — estrategia y justificación

- **Documentos con headers Markdown** (`.md`/`.txt` con `##`): split por estructura (`MarkdownHeaderTextSplitter`) + `RecursiveCharacterTextSplitter` dentro de cada sección.
- **Documentos sin headers** (páginas de PDF, `.docx` plano): `RecursiveCharacterTextSplitter` directo.
- **Config elegida:** `chunk_size=800`, `chunk_overlap=120`. Validado empíricamente en la Tarea 1: con `chunk_size=400` una lista de 4 principios quedaba cortada entre 2 chunks; con 800 se mantiene completa. Ver detalle en `load_documents.py`.

## Entregables de la tarea

1. **URL del servicio desplegado** → (completar tras `fly deploy`)
2. **`load_documents.py`** — código de carga + estrategia de chunking documentada (este archivo)
3. **Preguntas respondibles** → `eval/preguntas_respondibles.md`
4. **Preguntas no respondibles** → `eval/preguntas_no_respondibles.md`