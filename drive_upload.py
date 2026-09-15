from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
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

# Reintentos por tarjeta.
MAX_ATTEMPTS = 4

# Una segunda pasada intenta solamente las que no pudieron subirse.
MAX_ROUNDS = 2

# Pequeña pausa entre archivos para no golpear Apps Script de forma seguida.
BETWEEN_FILES_SECONDS = 1.0

# Errores HTTP que consideramos temporales.
RETRYABLE_STATUS = {
    404,
    408,
    425,
    429,
    500,
    502,
    503,
    504,
}


def get_lima_today() -> str:
    if ZoneInfo is not None:
        try:
            return datetime.now(
                ZoneInfo("America/Lima")
            ).strftime("%Y-%m-%d")
        except Exception:
            pass

    return datetime.now().strftime("%Y-%m-%d")


def load_news() -> list[dict]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {DATA_FILE}"
        )

    data = json.loads(
        DATA_FILE.read_text(encoding="utf-8")
    )

    if not isinstance(data, list):
        raise ValueError(
            "data/noticias.json debe contener una lista."
        )

    if not data:
        raise ValueError(
            "data/noticias.json está vacío."
        )

    return data


def ensure_output_dir() -> None:
    if not OUTPUT_DIR.exists():
        raise FileNotFoundError(
            f"No existe la carpeta output: {OUTPUT_DIR}"
        )


def find_card_file(numero: str) -> Path | None:
    candidates = sorted(
        OUTPUT_DIR.glob(f"{numero}_*.png")
    )

    if not candidates:
        return None

    return candidates[0]


def build_payload(
    file_path: Path,
    date_str: str,
) -> dict:
    mime_type = (
        mimetypes.guess_type(file_path.name)[0]
        or "image/png"
    )

    content_base64 = base64.b64encode(
        file_path.read_bytes()
    ).decode("utf-8")

    return {
        "secret": UPLOAD_SECRET,
        "date": date_str,
        "filename": file_path.name,
        "mimeType": mime_type,
        "contentBase64": content_base64,
    }


def request_once(
    file_path: Path,
    date_str: str,
) -> dict:
    payload = build_payload(
        file_path,
        date_str,
    )

    response = requests.post(
        WEBAPP_URL,
        headers={
            "Content-Type": "application/json",
            "User-Agent": (
                "Gaming-News-Generator/1.0"
            ),
        },
        data=json.dumps(payload),
        timeout=180,
        allow_redirects=True,
    )

    # No hacemos raise_for_status todavía porque necesitamos
    # saber si el error es temporal y merece otro intento.
    if response.status_code >= 400:
        error = requests.HTTPError(
            (
                f"HTTP {response.status_code} "
                f"al subir {file_path.name}"
            ),
            response=response,
        )
        raise error

    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError(
            (
                "Apps Script devolvió una respuesta "
                f"no JSON para {file_path.name}"
            )
        ) from exc

    if not data.get("ok"):
        raise RuntimeError(
            (
                f"Apps Script respondió error para "
                f"{file_path.name}: {data}"
            )
        )

    return data


def is_retryable_error(exc: Exception) -> bool:
    if isinstance(
        exc,
        (
            requests.Timeout,
            requests.ConnectionError,
        ),
    ):
        return True

    if isinstance(exc, requests.HTTPError):
        response = exc.response

        if response is None:
            return True

        return (
            response.status_code
            in RETRYABLE_STATUS
        )

    return False


def upload_with_retry(
    file_path: Path,
    date_str: str,
) -> dict:
    last_error: Exception | None = None

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1,
    ):
        try:
            if attempt > 1:
                print(
                    f"  Reintento "
                    f"{attempt}/{MAX_ATTEMPTS}..."
                )

            result = request_once(
                file_path,
                date_str,
            )

            return result

        except Exception as exc:
            last_error = exc

            print(
                f"  Intento {attempt} falló: "
                f"{type(exc).__name__}: {exc}"
            )

            if (
                not is_retryable_error(exc)
                or attempt >= MAX_ATTEMPTS
            ):
                break

            # Espera progresiva:
            # 2 s -> 5 s -> 10 s
            wait_times = [2, 5, 10]

            wait_seconds = wait_times[
                min(
                    attempt - 1,
                    len(wait_times) - 1,
                )
            ]

            print(
                f"  Esperando {wait_seconds}s "
                "antes de reintentar..."
            )

            time.sleep(wait_seconds)

    if last_error is None:
        raise RuntimeError(
            f"Fallo desconocido: {file_path.name}"
        )

    raise last_error


def main() -> None:
    print()
    print("=" * 64)
    print(
        " NICOLAS HERNANDEZ - "
        "SUBIDA A GOOGLE DRIVE VÍA APPS SCRIPT V2 "
    )
    print("=" * 64)
    print()

    if not WEBAPP_URL:
        raise RuntimeError(
            "Falta DRIVE_WEBAPP_URL."
        )

    if not UPLOAD_SECRET:
        raise RuntimeError(
            "Falta UPLOAD_SECRET."
        )

    ensure_output_dir()

    news = load_news()
    date_str = get_lima_today()

    expected_files: list[Path] = []
    missing_cards: list[str] = []

    expected_numbers = [
        "00",
    ]

    for index, item in enumerate(
        news,
        start=1,
    ):
        numero = str(
            item.get("numero") or index
        ).zfill(2)

        expected_numbers.append(
            numero
        )

    expected_numbers.append(
        "07"
    )

    for numero in expected_numbers:
        local_path = find_card_file(
            numero
        )

        if local_path is None:
            missing_cards.append(
                numero
            )
        else:
            expected_files.append(
                local_path
            )

    print(
        f"Fecha de trabajo: {date_str}"
    )
    print(
        f"Noticias esperadas: {len(news)}"
    )
    print(
        "Piezas de carrusel esperadas: 8"
    )
    print(
        f"Tarjetas encontradas: "
        f"{len(expected_files)}"
    )

    if missing_cards:
        print(
            "Tarjetas locales faltantes: "
            + ", ".join(missing_cards)
        )

    print()

    pending = list(expected_files)
    uploaded_names: set[str] = set()
    final_errors: dict[str, str] = {}

    for round_number in range(
        1,
        MAX_ROUNDS + 1,
    ):
        if not pending:
            break

        print("-" * 64)
        print(
            f" RONDA DE SUBIDA "
            f"{round_number}/{MAX_ROUNDS} "
            f"({len(pending)} pendientes)"
        )
        print("-" * 64)
        print()

        next_pending: list[Path] = []

        for file_path in pending:
            print(
                f"Subiendo: {file_path.name}"
            )

            try:
                result = upload_with_retry(
                    file_path,
                    date_str,
                )

                filename = result.get(
                    "filename",
                    file_path.name,
                )

                file_id = result.get(
                    "fileId",
                    "",
                )

                print(
                    f"  ✅ OK: {filename}"
                )

                if file_id:
                    print(
                        f"  ID: {file_id}"
                    )

                uploaded_names.add(
                    file_path.name
                )

                final_errors.pop(
                    file_path.name,
                    None,
                )

            except Exception as exc:
                message = (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                final_errors[
                    file_path.name
                ] = message

                next_pending.append(
                    file_path
                )

                print(
                    "  ❌ No pudo subirse "
                    "en esta ronda."
                )

            # Evita peticiones consecutivas
            # demasiado rápidas a Apps Script.
            time.sleep(
                BETWEEN_FILES_SECONDS
            )

        pending = next_pending

        if pending and (
            round_number < MAX_ROUNDS
        ):
            print()
            print(
                "Habrá una segunda ronda "
                "solo para las tarjetas fallidas."
            )
            print()

            time.sleep(3)

    uploaded = len(uploaded_names)
    expected = len(news)

    print()
    print("=" * 64)
    print(" RESULTADO DE GOOGLE DRIVE ")
    print("=" * 64)
    print()
    print(
        f"Esperadas: {expected}"
    )
    print(
        f"Encontradas localmente: "
        f"{len(expected_files)}"
    )
    print(
        f"Subidas correctamente: {uploaded}"
    )
    print(
        f"Fallidas después de reintentos: "
        f"{len(pending)}"
    )

    if final_errors:
        print()
        print("Errores finales:")

        for filename, message in (
            final_errors.items()
        ):
            print(
                f"  - {filename}: {message}"
            )

    if missing_cards:
        print()
        print(
            "Faltaron tarjetas antes "
            "de intentar subir:"
        )

        for numero in missing_cards:
            print(
                f"  - Tarjeta {numero}"
            )

    print()

    # Éxito solamente si tenemos exactamente
    # todas las tarjetas esperadas.
    if (
        uploaded != expected
        or missing_cards
    ):
        raise RuntimeError(
            (
                "Google Drive incompleto: "
                f"{uploaded}/{expected} "
                "tarjetas subidas."
            )
        )

    print(
        "✅ Todas las tarjetas fueron "
        "subidas correctamente."
    )
    print(
        "✅ Google Drive actualizado."
    )


if __name__ == "__main__":
    main()