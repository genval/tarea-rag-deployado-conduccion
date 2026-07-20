"""
debug_chunking.py — Inspecciona el resultado del chunking SIN tocar Qdrant.

Útil para revisar, antes de indexar de verdad, cuántos chunks salen de cada
archivo y si el tamaño elegido corta contenido de forma rara.

Uso:
    python debug_chunking.py
"""

from load_documents import cargar_documentos, chunkear, CHUNK_SIZE, CHUNK_OVERLAP

documentos = cargar_documentos()
print(f"\nTotal documentos cargados: {len(documentos)}")

chunks = chunkear(documentos)
print(f"Total chunks generados: {len(chunks)} (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})\n")

# --- Cuántos chunks salieron de cada archivo fuente ---
por_archivo = {}
for c in chunks:
    archivo = c.metadata.get("archivo", "?")
    por_archivo[archivo] = por_archivo.get(archivo, 0) + 1

print("Chunks por archivo:")
for archivo, n in por_archivo.items():
    print(f"  {archivo}: {n} chunks")

# --- Muestra de los primeros 3 chunks completos, para revisar a ojo ---
print("\n--- Muestra de chunks (los primeros 3) ---")
for i, c in enumerate(chunks[:3]):
    print(f"\nChunk {i} · archivo={c.metadata.get('archivo')} · {len(c.page_content)} caracteres")
    print(c.page_content[:300], "...")

# --- Estadísticas de tamaño, para detectar chunks sospechosamente chicos o grandes ---
tamanos = [len(c.page_content) for c in chunks]
print(f"\nTamaño de chunk: min={min(tamanos)} · max={max(tamanos)} · "
      f"promedio={sum(tamanos)//len(tamanos)}")

muy_chicos = [c for c in chunks if len(c.page_content) < 50]
if muy_chicos:
    print(f"\n⚠️  {len(muy_chicos)} chunk(s) con menos de 50 caracteres (revisar si son ruido/basura):")
    for c in muy_chicos:
        print(f"   - '{c.page_content[:60]}' (archivo: {c.metadata.get('archivo')})")