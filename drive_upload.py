from __future__ import annotations

import base64
import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "noticias.json"
OUTPUT_DIR = BASE_DIR / "output"

load_dotenv(BASE_DIR / ".env", override=False)

WEBAPP_URL = os.getenv("DRIVE_WEBAPP_URL", "").strip()
UPLOAD_SECRET = os.getenv("UPLOAD_SECRET", "").strip()


def get_lima_today() -> str:
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo("America/Lima")).strftime("%Y-%m-%d")
        except Exception:
            pass
    return datetime.now().strftime("%Y-%m-%d")


def load_news() -> list[dict]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"No existe el archivo: {DATA_FILE}")

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("data/noticias.json debe contener una lista.")

    if not data:
        raise ValueError("data/noticias.json está vacío.")

    return data


def ensure_output_dir() -> None:
    if not OUTPUT_DIR.exists():
        raise FileNotFoundError(f"No existe la carpeta output: {OUTPUT_DIR}")


def find_card_file(numero: str) -> Path | None:
    candidates = sorted(OUTPUT_DIR.glob(f"{numero}_*.png"))
    if not candidates:
        return None
    return candidates[0]


def build_payload(file_path: Path, date_str: str) -> dict:
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    content_base64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")

    return {
        "secret": UPLOAD_SECRET,
        "date": date_str,
        "filename": file_path.name,
        "mimeType": mime_type,
        "contentBase64": content_base64,
    }


def upload_file(file_path: Path, date_str: str) -> dict:
    payload = build_payload(file_path, date_str)

    response = requests.post(
        WEBAPP_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=180,
    )

    response.raise_for_status()

    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError(
            f"La respuesta del Web App no es JSON válido para {file_path.name}"
        ) from exc

    if not data.get("ok"):
        raise RuntimeError(f"Respuesta no OK para {file_path.name}: {data}")

    return data


def main() -> None:
    print()
    print("=" * 64)
    print(" NICOLAS HERNANDEZ - SUBIDA A GOOGLE DRIVE VÍA APPS SCRIPT ")
    print("=" * 64)
    print()

    if not WEBAPP_URL:
        raise RuntimeError("Falta DRIVE_WEBAPP_URL en variables de entorno o en .env")

    if not UPLOAD_SECRET:
        raise RuntimeError("Falta UPLOAD_SECRET en variables de entorno o en .env")

    ensure_output_dir()
    news = load_news()
    expected_count = len(news)
    date_str = get_lima_today()

    print(f"Fecha de trabajo: {date_str}")
    print(f"Noticias esperadas: {expected_count}")
    print()

    print("-" * 64)
    print(f" SUBIENDO {expected_count} TARJETAS ")
    print("-" * 64)
    print()

    uploaded = 0
    missing = 0

    for index, item in enumerate(news, start=1):
        numero = str(item.get("numero") or index).zfill(2)
        local_path = find_card_file(numero)

        if not local_path:
            print(f"No encontrada: tarjeta {numero}")
            missing += 1
            continue

        result = upload_file(local_path, date_str)

        filename = result.get("filename", local_path.name)
        file_id = result.get("fileId", "")
        folder = result.get("folder", "IMAGENES")

        print(f"Subida: {filename}")
        if file_id:
            print(f"  ID: {file_id}")
        print(f"  Carpeta: {folder}")

        uploaded += 1

    print()
    print("=" * 64)
    print(" PROCESO TERMINADO ")
    print("=" * 64)
    print()
    print(f"Imágenes procesadas: {uploaded + missing}")
    print(f"Subidas: {uploaded}")
    print(f"No encontradas: {missing}")
    print()

    if uploaded == 0:
        raise RuntimeError("No se subió ninguna imagen.")

    print(f"✅ {uploaded} tarjetas enviadas al Web App.")
    print("✅ Google Drive actualizado mediante Apps Script.")


if __name__ == "__main__":
    main()