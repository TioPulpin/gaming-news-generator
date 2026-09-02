import io
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from PIL import Image


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

NEWS_FILE = BASE_DIR / "data" / "noticias.json"

CANDIDATES_FILE = (
    BASE_DIR / "data" / "image_candidates.json"
)

CONFIG_FILE = BASE_DIR / "image_config.json"

LIMA_TIMEZONE = ZoneInfo("America/Lima")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/152 Safari/537.36"
    )
}


# =========================================================
# CONFIG
# =========================================================

config = json.loads(
    CONFIG_FILE.read_text(
        encoding="utf-8"
    )
)

MIN_WIDTH = config.get(
    "minimum_width",
    800
)

MIN_HEIGHT = config.get(
    "minimum_height",
    450
)

TIMEOUT = config.get(
    "request_timeout_seconds",
    15
)


# =========================================================
# FECHA
# =========================================================

today = datetime.now(
    LIMA_TIMEZONE
).strftime("%Y-%m-%d")

DAILY_DIR = (
    BASE_DIR
    / "assets"
    / "daily"
    / today
)

DAILY_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# FUNCIONES
# =========================================================

def normalize_image(
    image,
    destination
):

    width, height = image.size

    if (
        width < MIN_WIDTH
        or height < MIN_HEIGHT
    ):

        raise ValueError(
            f"Imagen demasiado pequeña: "
            f"{width}x{height}"
        )

    # Convertimos todo a RGB para JPEG.
    if image.mode != "RGB":

        background = Image.new(
            "RGB",
            image.size,
            "black"
        )

        if image.mode in (
            "RGBA",
            "LA"
        ):

            background.paste(
                image,
                mask=image.getchannel("A")
            )

            image = background

        else:

            image = image.convert(
                "RGB"
            )

    image.save(
        destination,
        format="JPEG",
        quality=92,
        optimize=True
    )

    return width, height


def process_local_image(
    source,
    destination
):

    source_path = Path(
        source
    )

    if not source_path.is_absolute():

        source_path = (
            BASE_DIR
            / source_path
        )

    if not source_path.exists():

        raise FileNotFoundError(
            source_path
        )

    with Image.open(
        source_path
    ) as image:

        return normalize_image(
            image,
            destination
        )


def download_remote_image(
    url,
    destination
):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    with Image.open(
        io.BytesIO(
            response.content
        )
    ) as image:

        return normalize_image(
            image,
            destination
        )


# =========================================================
# CARGAR ARCHIVOS
# =========================================================

news = json.loads(
    NEWS_FILE.read_text(
        encoding="utf-8"
    )
)


if CANDIDATES_FILE.exists():

    candidates = json.loads(
        CANDIDATES_FILE.read_text(
            encoding="utf-8"
        )
    )

else:

    candidates = []


candidate_map = {
    str(
        item.get(
            "numero",
            ""
        )
    ): item

    for item in candidates
}


# =========================================================
# PROCESAR
# =========================================================

print()
print("==============================================")
print(" GAMING NEWS GENERATOR - PREPARAR IMÁGENES")
print("==============================================")
print()

print(
    f"Carpeta diaria: {DAILY_DIR}"
)

print()


processed = 0
missing = 0


for index, item in enumerate(
    news,
    start=1
):

    numero = item.get(
        "numero",
        f"{index:02d}"
    )

    destination = (
        DAILY_DIR
        / f"{numero}.jpg"
    )

    local_image = item.get(
        "imagen",
        ""
    )

    candidate = candidate_map.get(
        str(numero),
        {}
    )

    candidate_url = candidate.get(
        "image_candidate_url",
        ""
    )

    candidate_source = candidate.get(
        "image_source",
        ""
    )

    candidate_source_url = candidate.get(
        "image_source_url",
        ""
    )

    candidate_source_type = candidate.get(
        "source_type",
        ""
    )

    print(
        f'{numero}. {item.get("titulo", "")}'
    )


    # -----------------------------------------------------
    # OPCIÓN 1: IMAGEN LOCAL
    # -----------------------------------------------------

    if local_image:

        try:

            width, height = process_local_image(
                local_image,
                destination
            )

            relative_path = (
                destination
                .relative_to(BASE_DIR)
                .as_posix()
            )

            item["imagen"] = relative_path

            item["imagenFuente"] = (
                candidate_source
            )

            item["imagenFuenteUrl"] = (
                candidate_source_url
            )

            item["imagenTipo"] = (
                candidate_source_type
            )

            processed += 1

            print(
                f"    Local OK: {width}x{height}"
            )

            print(
                f"    Guardada: {relative_path}"
            )

            print()

            continue

        except Exception as error:

            print(
                f"    Local inválida: {error}"
            )


    # -----------------------------------------------------
    # OPCIÓN 2: URL CANDIDATA
    # -----------------------------------------------------

    if candidate_url:

        try:

            width, height = download_remote_image(
                candidate_url,
                destination
            )

            relative_path = (
                destination
                .relative_to(BASE_DIR)
                .as_posix()
            )

            item["imagen"] = relative_path

            processed += 1

            print(
                f"    Descarga OK: {width}x{height}"
            )

            print(
                f"    Guardada: {relative_path}"
            )

            print()

            continue

        except Exception as error:

            print(
                f"    Descarga inválida: {error}"
            )


    # -----------------------------------------------------
    # SIN IMAGEN
    # -----------------------------------------------------

    item["imagen"] = ""

    missing += 1

    print(
        "    SIN IMAGEN RESUELTA"
    )

    print()


# =========================================================
# ACTUALIZAR noticias.json
# =========================================================

NEWS_FILE.write_text(
    json.dumps(
        news,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


# =========================================================
# RESULTADO
# =========================================================

print("==============================================")
print(" RESULTADO")
print("==============================================")
print()

print(
    f"Imágenes preparadas: {processed}"
)

print(
    f"Sin imagen: {missing}"
)

print()

print(
    f"Carpeta:"
)

print(
    DAILY_DIR
)

print()

print(
    "✅ No se utilizó IA."
)

print(
    "✅ Costo API: $0.00"
)

print()