# Cómo correr este proyecto localmente (paso a paso)

Guía pensada para alguien que nunca ha tocado este repo — sin asumir conocimiento previo.

---

## 0. Lo que necesitas tener instalado antes de empezar

- **Git** — para descargar el proyecto.
- **Python 3.11 o superior** — el lenguaje en que está escrito.
- **Poetry** — administra las librerías que el proyecto necesita.

Verifica si ya los tienes, abriendo una terminal y corriendo:
```bash
git --version
python --version
poetry --version
```
Si alguno falla, instálalo primero (busca "instalar Git", "instalar Python" o "instalar Poetry" para tu sistema operativo) antes de seguir.

> 💡 **Windows + Anaconda:** si instalaste Poetry dentro de un entorno de Anaconda,
> es común que funcione en **Anaconda Prompt** pero no en la terminal de VS Code
> (PowerShell) — cada terminal nueva que abras en VS Code puede no tener a Poetry
> en su PATH. Si te sale `poetry: command not found` ahí, corre esto primero
> (ajusta la ruta a la tuya, la obtienes con `where poetry` en Anaconda Prompt):
> ```powershell
> $env:Path += ";C:\Users\Gisse\anaconda3\Scripts"
> ```
> Esto hay que repetirlo **cada vez que abras una terminal nueva** en VS Code. Si
> te cansa repetirlo, puedes dejarlo permanente: busca "Variables de entorno" en
> el menú de inicio de Windows → *Editar las variables de entorno del sistema* →
> *Variables de entorno...* → en tu usuario, selecciona `Path` → *Editar* →
> *Nuevo* → pega la misma ruta → Aceptar todo → **cierra y vuelve a abrir VS Code
> por completo** (no basta con una terminal nueva).

---

## 1. Descargar el proyecto

```bash
git clone https://github.com/genval/tarea-rag-deployado-conduccion.git
cd tarea-rag-deployado-conduccion
```

---

## 2. Crear tu archivo de credenciales (`.env`)

El repo trae un archivo de ejemplo, pero **sin las claves reales** (por seguridad, nunca se suben a GitHub). Cópialo:

```bash
copy .env.example .env
```
*(en Mac/Linux el comando es `cp .env.example .env`)*

Abre el archivo `.env` recién creado en cualquier editor de texto (o en VS Code) y complétalo con tus 3 credenciales reales:

```
OPENAI_API_KEY=tu_key_de_openai_aqui
QDRANT_URL=tu_url_de_qdrant_aqui
QDRANT_API_KEY=tu_key_de_qdrant_aqui
```

- **OpenAI:** consíguela en https://platform.openai.com/api-keys
- **Qdrant:** créala en https://cloud.qdrant.io (cuenta gratis) → crea un cluster → copia la URL y genera una API key.

---

## 3. Instalar las dependencias del proyecto

Dentro de la carpeta del proyecto:

```bash
poetry install --with dev
```

Esto puede tardar unos minutos la primera vez (descarga todas las librerías necesarias: FastAPI, LangChain, LangGraph, etc.).

**Si el comando `poetry` no se reconoce:** puede que necesites instalarlo primero con `pip install poetry`, o que tu terminal no tenga a Poetry en el PATH — en ese caso, prueba abriendo una terminal nueva, o busca "agregar poetry al PATH de Windows/Mac" según tu sistema.

---

## 4. Poblar la base de datos vectorial (Qdrant)

> ⚠️ **Este paso ya se hizo.** Si estás trabajando en equipo y otra persona ya corrió este paso con las mismas credenciales de Qdrant que tú tienes en tu `.env`, **NO vuelvas a correrlo** — sáltate directo al Paso 5.
>
> **Por qué importa:** `load_documents.py` usa `recreate_collection`, que **borra y reconstruye** la colección desde cero. Si dos personas lo corren al mismo tiempo (o sin coordinarse), pueden pisarse entre sí y generar errores temporales o confusión sobre qué datos hay realmente indexados. Solo la persona "dueña" del índice debería correrlo — el resto solo *consulta* la colección que ya existe.

Si en tu caso **sí** te corresponde poblar Qdrant por primera vez (por ejemplo, cambiaron las fuentes o es tu primera vez configurando el proyecto), este paso lee los documentos de la carpeta `data/`, los trocea, y los sube a tu Qdrant Cloud.

Opcional pero recomendado — revisar el chunking antes de subir nada:
```bash
poetry run python debug_chunking.py
```

Y luego, indexar de verdad:
```bash
poetry run python load_documents.py
```

Al final deberías ver un mensaje como:
```
✅ Índice listo · 208 vectores en Qdrant/tarea2_conduccion_multiformato (COSINE, 256d)
```

---

## 5. Levantar el servidor

```bash
poetry run uvicorn app.server:app --reload --port 8000
```

Deberías ver en la terminal:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Deja esa terminal abierta** — mientras esté corriendo ahí, el servidor está "vivo". Para detenerlo en cualquier momento: `Ctrl + C`.

---

## 6. Probarlo

Abre tu navegador en:
```
http://localhost:8000/docs
```

Vas a ver una página con la lista de endpoints (esto se llama Swagger, es la interfaz de prueba automática de FastAPI).

1. Busca **`POST /ask`** y haz clic para expandirlo.
2. Clic en el botón **"Try it out"**.
3. En el cuadro de texto, reemplaza el contenido por algo como:
   ```json
   { "pregunta": "¿Cuáles son los 4 principios del Sistema Seguro?" }
   ```
4. Clic en **"Execute"**.
5. Baja hasta **"Response body"** — ahí aparece la respuesta del agente.

Para probar que **no inventa** respuestas, intenta con una pregunta que no está en los documentos, por ejemplo:
```json
{ "pregunta": "¿Cuál es la velocidad máxima permitida en autopistas en Chile?" }
```
Debería responder algo como *"No tengo información suficiente para responder esa pregunta."*

---

## 7. (Opcional) Correr todas las preguntas de evaluación de una vez

En vez de probar pregunta por pregunta en `/docs`, puedes correr automáticamente **todo** el set de `eval/` (respondibles + no respondibles) contra el servidor.

**Con el servidor del Paso 5 corriendo en una terminal**, abre **otra terminal nueva** (recuerda: si usas Poetry vía Anaconda en Windows, puede que necesites agregar Poetry al PATH de esta terminal nueva también) y corre:

```bash
poetry run python test_eval.py
```

Vas a ver cada pregunta con su respuesta, marcada con ✓ (se comportó como se esperaba) o ✗ (revisar). Tarda un rato porque son ~27 preguntas, una por una.

---

## Problemas comunes

| Síntoma | Causa probable |
|---|---|
| `poetry: command not found` (en terminal de VS Code, pero sí funciona en Anaconda Prompt) | Ver la nota en el Paso 0 — corre `$env:Path += ";C:\Users\Gisse\anaconda3\Scripts"` en esa terminal |
| Error pidiendo `OPENAI_API_KEY` / `QDRANT_URL` / `QDRANT_API_KEY` | El archivo `.env` no existe o está incompleto — revisa el Paso 2 |
| El agente responde con error 502 | Revisa el log de la terminal del servidor — suele ser un problema de configuración del modelo o la API key |