"""
test_eval.py — Corre TODAS las preguntas de eval/ contra el servidor local,
para revisar de un vistazo si las respondibles se responden bien y las
no-respondibles dicen "no tengo información".

Requiere que el servidor ya esté corriendo en otra terminal:
    poetry run uvicorn app.server:app --reload --port 8000

Uso:
    poetry run python test_eval.py
"""

import re
import time
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"
EVAL_DIR = Path(__file__).parent / "eval"


def extraer_preguntas(archivo: Path) -> list[str]:
    """Extrae las preguntas de un archivo .md con formato '1. pregunta...'"""
    texto = archivo.read_text(encoding="utf-8")
    return re.findall(r"^\d+\.\s+(.+)$", texto, flags=re.MULTILINE)


def preguntar(pregunta: str) -> str:
    try:
        r = requests.post(f"{BASE_URL}/ask", json={"pregunta": pregunta}, timeout=60)
        r.raise_for_status()
        return r.json()["respuesta"]
    except Exception as e:
        return f"[ERROR] {e}"


def correr_set(nombre: str, preguntas: list[str], se_espera_no_respuesta: bool = False):
    print(f"\n{'='*90}\n{nombre} ({len(preguntas)} preguntas)\n{'='*90}")
    for i, p in enumerate(preguntas, 1):
        respuesta = preguntar(p)
        dice_no_se = "no tengo información" in respuesta.lower()
        if se_espera_no_respuesta:
            marca = "✓" if dice_no_se else "✗ (debería haber dicho 'no tengo información')"
        else:
            marca = "✗ (dijo 'no tengo información' pero SÍ debería poder responder)" if dice_no_se else "✓"
        print(f"\n[{i}] {marca}")
        print(f"P: {p}")
        print(f"R: {respuesta}")
        time.sleep(0.3)  # no saturar el servidor local


if __name__ == "__main__":
    respondibles = extraer_preguntas(EVAL_DIR / "preguntas_respondibles.md")
    no_respondibles = extraer_preguntas(EVAL_DIR / "preguntas_no_respondibles.md")

    correr_set("PREGUNTAS RESPONDIBLES", respondibles, se_espera_no_respuesta=False)
    correr_set("PREGUNTAS NO RESPONDIBLES", no_respondibles, se_espera_no_respuesta=True)

    print(f"\n{'='*90}\nListo. Revisa arriba cualquier línea marcada con ✗\n{'='*90}")