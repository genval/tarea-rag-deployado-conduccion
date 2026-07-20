# Observabilidad con Langfuse (rama `feature/langfuse`)

> Esta funcionalidad **no está en `main`** — vive solo en esta rama, como un extra
> para aprender/experimentar. No es requisito de la Tarea RAG (3 semanas).

## Qué hace

Cada llamada al Agente Retriever queda registrada como un **trace** navegable en
Langfuse: qué herramienta llamó (`buscar_en_documento`), con qué argumentos,
cuánto tardó cada paso, y la respuesta final del LLM. Útil para depurar y para
entender qué hace el agente por dentro, más allá del texto de la respuesta.

Es **opcional y degradante**: si no hay claves de Langfuse en el `.env`, el
servidor sigue funcionando exactamente igual, solo que sin trazas.

## Setup — Langfuse local (con Docker)

Se usa una instancia de Langfuse corriendo en tu propio computador vía Docker
Compose. **Se instala en una carpeta aparte, fuera de este repo** (es un
proyecto independiente, no una librería):

```bash
cd ..                      # sal de este repo
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up
```

La primera vez tarda varios minutos (baja Postgres, ClickHouse, Redis, etc.).
Cuando esté listo, abre **http://localhost:3000**, crea tu cuenta local, una
organización, y un proyecto (ej. `langserve-rag-agente`).

> ⚠️ **Conflicto de puertos conocido:** si al hacer `docker compose up` sale un
> error de `bind: only one usage of each socket address...` en el puerto 9000,
> es porque otro proceso en tu máquina (frecuentemente un kernel de Jupyter) ya
> lo está usando. Solución: edita `docker-compose.yml`, en el bloque `clickhouse`,
> y cambia la línea `127.0.0.1:9000:9000` por algo como `127.0.0.1:19000:9000`
> (solo el número de la izquierda). Vuelve a intentar `docker compose up`.

## Generar las API keys

Dentro de tu proyecto en Langfuse: **Settings → API Keys → Create new API key**.
Copia el **Public Key** (`pk-lf-...`) y el **Secret Key** (`sk-lf-...`, se
muestra una sola vez).

## Configurar el `.env` de este proyecto

Agrega estas 3 líneas a tu `.env` (junto a `OPENAI_API_KEY`, `QDRANT_URL`, etc.):

```
LANGFUSE_PUBLIC_KEY=pk-lf-tu_public_key
LANGFUSE_SECRET_KEY=sk-lf-tu_secret_key
LANGFUSE_BASE_URL=http://localhost:3000
```

## Instalar dependencias (solo en esta rama)

```bash
poetry add langfuse langchain
```

(`langchain` —el paquete general, no solo `langchain-core`— es necesario
porque `langfuse.langchain.CallbackHandler` depende de él.)

## Verificar que funciona

1. Levanta el servidor como siempre:
   ```bash
   poetry run uvicorn app.server:app --reload --port 8000
   ```
2. Al arrancar, deberías ver en la terminal:
   ```
   ✅ Langfuse activo → http://localhost:3000
   ```
   Si en cambio ves una advertencia (`⚠️`), revisa el mensaje de error — casi
   siempre es una clave mal copiada o el `LANGFUSE_BASE_URL` apuntando a un
   lugar equivocado.
3. Prueba `POST /ask` en `http://localhost:8000/docs`.
4. Ve a tu proyecto en Langfuse → pestaña **Traces** → deberías ver la corrida,
   con el árbol completo (`agent` → `tools` → `buscar_en_documento` → respuesta).

## Sobre local vs. Cloud

Esta guía usa **Langfuse local** porque es la vía que enseña el curso y no
depende de crear cuenta en un servicio externo. Pero si en algún momento este
servidor se despliega en fly.io (como en `main`), Langfuse local **no serviría**
para monitorear esa instancia pública — tu Docker local no es accesible desde
internet. Para eso habría que migrar a **Langfuse Cloud**
(`https://cloud.langfuse.com`), cambiando solo `LANGFUSE_BASE_URL` y generando
las keys ahí — el resto del código no cambia.

## Apagar Langfuse

Desde la carpeta donde clonaste `langfuse/`:
```bash
docker compose down       # detiene, conserva los datos
docker compose up         # lo vuelve a levantar con tus proyectos y claves
```
Para borrar todo (datos incluidos): `docker compose down -v`.