# Observabilidad con Langfuse (rama `feature/langfuse`)

> Esta funcionalidad **no está en `main`** — vive solo en esta rama, como un extra
> para aprender/experimentar. No es requisito de la Tarea RAG (3 semanas).

## Qué hace

Cada llamada al Agente Retriever queda registrada como un **trace** navegable en
Langfuse: qué herramienta llamó (`buscar_en_documento`), con qué argumentos,
cuánto tardó cada paso, tokens usados, costo en USD, y la respuesta final del
LLM. Útil para depurar y para entender qué hace el agente por dentro, más allá
del texto de la respuesta.

Es **opcional y degradante**: si no hay claves de Langfuse en el `.env`, el
servidor sigue funcionando exactamente igual, solo que sin trazas.

## Setup — Langfuse Cloud

Se usa **Langfuse Cloud** (`https://cloud.langfuse.com`), no una instancia local
con Docker — porque este servidor se despliega en fly.io (público, 24/7), y un
Langfuse corriendo en el Docker de tu propio computador no sería accesible desde
ahí una vez desplegado. Cloud, en cambio, funciona igual sin importar si el
servidor corre localmente o ya está en producción.

1. Ve a **https://cloud.langfuse.com** y crea una cuenta (o inicia sesión si ya
   tienes una de otra tarea del curso).
2. Crea un **proyecto nuevo**, específico para esta tarea (ej.
   `tarea-rag-deployado-conduccion`) — así sus trazas no se mezclan con las de
   otros proyectos que tengas.
3. Dentro del proyecto: **Settings → API Keys → Create new API key**. Copia el
   **Public Key** (`pk-lf-...`) y el **Secret Key** (`sk-lf-...`, se muestra una
   sola vez).

> ⚠️ **Las keys son específicas de cada proyecto**, no generales de tu cuenta.
> Si usas keys de otro proyecto (por ejemplo, copiadas de una tarea anterior),
> `auth_check()` pasará igual (son válidas), pero las trazas van a llegar al
> proyecto equivocado — vas a ver "Waiting for first trace" eternamente en el
> proyecto que sí estás mirando. Genera las keys **desde dentro** del proyecto
> correcto para evitar esto.

## Configurar el `.env` de este proyecto

Agrega estas 3 líneas a tu `.env` (junto a `OPENAI_API_KEY`, `QDRANT_URL`, etc.):

```
LANGFUSE_PUBLIC_KEY=pk-lf-tu_public_key
LANGFUSE_SECRET_KEY=sk-lf-tu_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

> Si tu proyecto quedó en la región **US** en vez de EU, la URL cambia a
> `https://us.cloud.langfuse.com` — usa la misma que aparece en la barra de tu
> navegador cuando entras a tu proyecto.

## Instalar dependencias (solo en esta rama)

```bash
poetry add langfuse langchain
```

(`langchain` —el paquete general, no solo `langchain-core`— es necesario
porque `langfuse.langchain.CallbackHandler` depende de él.)

## Un problema común: variables de entorno "pegadas" de otro proyecto

Si trabajas con varios proyectos abiertos en VS Code, es posible que tu sesión
de terminal ya tenga variables `LANGFUSE_*` cacheadas de otro proyecto — y por
defecto, `load_dotenv()` **no sobrescribe** variables que ya existen en la
sesión, así que tu `.env` local pierde silenciosamente contra eso.

**Síntoma:** todo parece funcionar (`✅ Langfuse activo...`, sin errores), pero
las trazas no aparecen en el proyecto que esperas — están yendo a otro.

**Ya está resuelto en el código:** `server.py` y `load_documents.py` usan
`load_dotenv(override=True)`, que fuerza a que el `.env` de este proyecto
siempre gane, sin importar qué haya cacheado la sesión. Si por alguna razón
sigue pasando igual, como diagnóstico manual (temporal, solo para esa sesión):
```powershell
Remove-Item Env:\LANGFUSE_PUBLIC_KEY -ErrorAction SilentlyContinue
Remove-Item Env:\LANGFUSE_SECRET_KEY -ErrorAction SilentlyContinue
Remove-Item Env:\LANGFUSE_BASE_URL -ErrorAction SilentlyContinue
```

## Configurar el precio del modelo (opcional, para ver el costo en USD)

Por defecto, Langfuse no calcula el costo en dólares de `gpt-5.4-mini` porque no
lo tiene en su lista de modelos predefinidos — solo muestra tokens. Si quieres
ver el costo, cada persona debe configurarlo en **su propio** proyecto de
Langfuse Cloud (esta config vive en la base de datos de Langfuse, no se
comparte vía Git — cada integrante del equipo debe repetirlo si usa su propia
cuenta/proyecto):

1. Ve a **Settings → Models → Create Model**.
2. **Regular expression:**
   ```
   (?i)^(gpt-5\.4-mini.*)$
   ```
   (el `.*` al final es necesario porque el modelo real incluye un sufijo de
   fecha, ej. `gpt-5.4-mini-2026-03-17` — sin el `.*` el regex nunca hace match)
3. **Prices** (valores de https://platform.openai.com/docs/pricing, tier "Short context",
   convertidos a precio por token = precio por 1M / 1,000,000):

   | Usage type | Precio |
   |---|---|
   | `input` | `0.00000075` |
   | `output` | `0.0000045` |
   | `input_cached_tokens` | `0.000000075` |
   | `output_reasoning_tokens` | `0.0000045` |

4. Revisa el "Price Preview" — la columna "per 1M" debe coincidir exactamente
   con los precios oficiales de OpenAI ($0.75 / $4.50 / $0.075 / $4.50).
5. **Submit.**

Esto solo aplica a trazas **nuevas** desde el momento en que lo guardas — las
trazas anteriores no se recalculan retroactivamente.

## Verificar que funciona

1. Levanta el servidor como siempre:
   ```bash
   poetry run uvicorn app.server:app --reload --port 8000
   ```
2. Al arrancar, deberías ver en la terminal:
   ```
   ✅ Langfuse activo → https://cloud.langfuse.com
   ```
   Si en cambio ves una advertencia (`⚠️`), revisa el mensaje de error — casi
   siempre es una clave mal copiada, vencida, o de otro proyecto.
3. Prueba `POST /ask` en `http://localhost:8000/docs`.
4. Ve a tu proyecto en https://cloud.langfuse.com → pestaña **Traces** →
   deberías ver la corrida, con el árbol completo
   (`agent` → `tools` → `buscar_en_documento` → respuesta).

## Alternativa: Langfuse local (si prefieres no depender de la nube para pruebas)

Es posible correr Langfuse en tu propio Docker en vez de Cloud — útil solo
mientras pruebas en tu compu, ya que **no sirve una vez que el servidor esté
desplegado en fly.io** (tu Docker local no es accesible desde internet).

```bash
cd ..                      # sal de este repo
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up
```

Abre **http://localhost:3000**, crea cuenta/proyecto local, y usa
`LANGFUSE_BASE_URL=http://localhost:3000` en tu `.env` en vez de la URL de
Cloud — el resto del código no cambia.

> ⚠️ **Conflicto de puertos conocido:** si `docker compose up` falla con
> `bind: only one usage of each socket address...` en el puerto 9000, es porque
> otro proceso (frecuentemente un kernel de Jupyter) ya lo está usando.
> Solución: en `docker-compose.yml`, bloque `clickhouse`, cambia
> `127.0.0.1:9000:9000` por `127.0.0.1:19000:9000` (solo el número de la
> izquierda) y reintenta.

Para apagarlo: `docker compose down` (conserva datos) o `docker compose down -v`
(borra todo).