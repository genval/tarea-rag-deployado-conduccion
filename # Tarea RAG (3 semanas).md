# Tarea RAG (3 semanas)

## Desafío

Expandir el repositorio del tutorial de **LangServe** ya generado y usar como cadena un **Agente Retriever** que consuma una instancia externa de una base de datos vectorial (se sugiere **Qdrant**).

La base de datos vectorial debe estar poblada previamente (con el contenido que ustedes elijan).

### Actividades

1. Crear una cuenta en Qdrant.
2. Obtener la **URL** y **API Key** de Qdrant.
3. Ejecutar la carga de documentos mediante un script independiente.
4. Modificar el código del servidor y reemplazar el runnable por el agente Retriever.
5. Desplegar la aplicación, agregando la URL y la API Key como secretos.

---

# Paso 1: Preparación de Fuentes de Datos

## 🎯 Objetivo Principal

Implementar un sistema **RAG** completo utilizando el stack tecnológico 2025:

- LangChain
- Qdrant Cloud
- OpenAI

Aplicando estrategias de **chunking inteligente** y una evaluación rigurosa del sistema.

## 📚 Requisitos mínimos

Seleccionar **2 o 3 fuentes de datos textuales** de diferentes tipos:

- Documentos PDF
- Documentos Word (.docx)
- Archivos de texto (.txt)

Los documentos deben pertenecer a un mismo dominio temático (por ejemplo: documentación técnica, libros, artículos especializados, etc.).

---

# Paso 2: Procesamiento y Chunking Estratégico

## 🔧 Implementar

### 1. Análisis del contenido

Determinar el tipo de documento y su estructura.

### 2. Selección de estrategia

Elegir una de las técnicas vistas en clase:

- RecursiveCharacterTextSplitter (baseline)
- SemanticChunker (avanzado)
- Chunking específico según el tipo de documento
- Otra estrategia debidamente justificada

### 3. Configuración optimizada

Definir:

- `chunk_size`
- `chunk_overlap`
- Separadores

---

# Paso 3: Indexación en Qdrant Cloud

## 🗄️ Crear un Vector Store

### Configuración

- Crear una colección de Qdrant con un nombre descriptivo.

### Metadata enriquecida

Generar metadata para cada chunk.

### Embeddings

Utilizar embeddings de OpenAI:

- `text-embedding-3-large`
- `text-embedding-3-small`

Seleccionar apropiadamente la cantidad de dimensiones.

### Evidencia

Mostrar la colección de Qdrant con la información cargada.

---

# Paso 4: Implementación del Sistema RAG

## 🤖 Implementar un sistema RAG funcional

Debe incluir:

- Retriever configurado con un valor apropiado de **top-k**.
- Prompt Template optimizado siguiendo las mejores prácticas vistas en el curso.
- Cadena RAG completa utilizando:
  - LangChain LCEL, o
  - LangGraph.

---

# Paso 5: Evaluación Sistemática

## 🧪 Crear datasets de evaluación

### Preguntas respondibles (10–15)

Preguntas que **sí pueden responderse** utilizando la información indexada.

### Preguntas no respondibles (5–10)

Preguntas sobre temas **no cubiertos** por los documentos.

El sistema debe responder apropiadamente con un mensaje similar a:

> "No tengo información suficiente."

---

# Entrega

## 📅 Deadline

**Domingo 02 de agosto a las 23:59**

## 📦 Entregables

1. URL del servicio desplegado.
2. Archivo con el código de carga de documentos a Qdrant, explicando:
   - la estrategia de chunking utilizada,
   - la razón de dicha estrategia.
3. Set de preguntas respondibles.
4. Set de preguntas no respondibles.