import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

DATA_FILE = BASE_DIR / "data" / "noticias.json"
OUTPUT_DIR = BASE_DIR / "output"

SCOPES = [
    "https://www.googleapis.com/auth/drive.file"
]

FOLDER_MIME = "application/vnd.google-apps.folder"

# ID de la carpeta raíz de Drive usada por el proyecto.
# Puedes renombrar esa carpeta en Google Drive sin cambiar este ID.
NEWS_FOLDER_ID = "1fQLJFzli2j8zK9huV3epfRqqwUUHwUAy"

EXPECTED_COUNT = 6

# Hora oficial del proyecto.
LIMA_TIMEZONE = ZoneInfo("America/Lima")


# =========================================================
# MESES
# =========================================================

MESES = {
    1: "01 - ENERO",
    2: "02 - FEBRERO",
    3: "03 - MARZO",
    4: "04 - ABRIL",
    5: "05 - MAYO",
    6: "06 - JUNIO",
    7: "07 - JULIO",
    8: "08 - AGOSTO",
    9: "09 - SEPTIEMBRE",
    10: "10 - OCTUBRE",
    11: "11 - NOVIEMBRE",
    12: "12 - DICIEMBRE",
}


# =========================================================
# AUTENTICACIÓN
# =========================================================

def get_credentials():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )

    if not creds or not creds.valid:

        if (
            creds
            and creds.expired
            and creds.refresh_token
        ):
            creds.refresh(
                Request()
            )

        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "No se encontró credentials.json"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES,
            )

            creds = flow.run_local_server(
                port=0
            )

        TOKEN_FILE.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

    return creds


# =========================================================
# UTILIDADES
# =========================================================

def escape_query(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
    )


def slugify(text):
    text = (
        text
        or ""
    ).strip().lower()

    text = re.sub(
        r"[^\w\s-]",
        "",
        text,
        flags=re.UNICODE,
    )

    text = re.sub(
        r"[\s_-]+",
        "_",
        text,
    )

    return (
        text.strip("_")
        or "noticia"
    )


# =========================================================
# CARPETAS
# =========================================================

def find_folder(
    service,
    name,
    parent_id,
):
    safe_name = escape_query(
        name
    )

    query = (
        f"name='{safe_name}' "
        f"and mimeType='{FOLDER_MIME}' "
        f"and trashed=false "
        f"and '{parent_id}' in parents"
    )

    result = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
        )
        .execute()
    )

    folders = result.get(
        "files",
        [],
    )

    if folders:
        return folders[0]["id"]

    return None


def create_folder(
    service,
    name,
    parent_id,
):
    metadata = {
        "name": name,
        "mimeType": FOLDER_MIME,
        "parents": [
            parent_id
        ],
    }

    folder = (
        service.files()
        .create(
            body=metadata,
            fields="id, name",
        )
        .execute()
    )

    print(
        f"Carpeta creada: {name}"
    )

    return folder["id"]


def find_or_create_folder(
    service,
    name,
    parent_id,
):
    folder_id = find_folder(
        service,
        name,
        parent_id,
    )

    if folder_id:
        print(
            f"Carpeta encontrada: {name}"
        )

        return folder_id

    return create_folder(
        service,
        name,
        parent_id,
    )


# =========================================================
# ARCHIVOS
# =========================================================

def find_file(
    service,
    filename,
    parent_id,
):
    safe_name = escape_query(
        filename
    )

    query = (
        f"name='{safe_name}' "
        f"and trashed=false "
        f"and '{parent_id}' in parents"
    )

    result = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
        )
        .execute()
    )

    files = result.get(
        "files",
        [],
    )

    if files:
        return files[0]

    return None


def find_file_by_number_prefix(
    service,
    numero,
    parent_id,
):
    prefix = f"{numero}_"

    query = (
        f"trashed=false "
        f"and '{parent_id}' in parents"
    )

    result = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            pageSize=100,
        )
        .execute()
    )

    files = result.get(
        "files",
        [],
    )

    matches = [
        item
        for item in files
        if str(
            item.get(
                "name",
                "",
            )
        ).startswith(
            prefix
        )
    ]

    if matches:
        return matches[0]

    return None


def upload_or_update_file(
    service,
    local_path,
    parent_id,
    numero,
):
    filename = local_path.name

    existing = find_file(
        service,
        filename,
        parent_id,
    )

    if existing is None:
        existing = find_file_by_number_prefix(
            service,
            numero,
            parent_id,
        )

    media = MediaFileUpload(
        str(local_path),
        mimetype="image/png",
        resumable=False,
    )

    if existing:
        previous_name = existing.get(
            "name",
            filename,
        )

        (
            service.files()
            .update(
                fileId=existing["id"],
                body={
                    "name": filename
                },
                media_body=media,
                fields="id, name",
            )
            .execute()
        )

        if previous_name == filename:
            print(
                f"Actualizada: {filename}"
            )
        else:
            print(
                f"Reemplazada: {previous_name}"
            )
            print(
                f"         por: {filename}"
            )

        return (
            existing["id"],
            "updated",
        )

    metadata = {
        "name": filename,
        "parents": [
            parent_id
        ],
    }

    result = (
        service.files()
        .create(
            body=metadata,
            media_body=media,
            fields="id, name",
        )
        .execute()
    )

    print(
        f"Subida: {filename}"
    )

    return (
        result["id"],
        "created",
    )


# =========================================================
# CARGAR NOTICIAS
# =========================================================

def load_news():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"No existe {DATA_FILE}"
        )

    items = json.loads(
        DATA_FILE.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        items,
        list,
    ):
        raise ValueError(
            "data/noticias.json debe contener una lista."
        )

    if len(items) != EXPECTED_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_COUNT} noticias "
            f"y se encontraron {len(items)}."
        )

    return items


# =========================================================
# MAIN
# =========================================================

def main():
    items = load_news()

    now = datetime.now(
        LIMA_TIMEZONE
    )

    year_name = str(
        now.year
    )

    month_name = MESES[
        now.month
    ]

    day_name = now.strftime(
        "%Y-%m-%d"
    )

    credentials = get_credentials()

    service = build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )

    print()
    print("=" * 64)
    print(
        " NICOLAS HERNANDEZ - SUBIDA A GOOGLE DRIVE V2.1"
    )
    print("=" * 64)
    print()

    print(
        f"Fecha de trabajo: {day_name}"
    )

    print(
        f"Noticias esperadas: {EXPECTED_COUNT}"
    )

    print()

    # -----------------------------------------------------
    # ESTRUCTURA:
    #
    # CARPETA RAÍZ
    # └── 2026
    #     └── 09 - SEPTIEMBRE
    #         └── 2026-09-02
    #             └── IMAGENES
    # -----------------------------------------------------

    year_folder = find_or_create_folder(
        service,
        year_name,
        NEWS_FOLDER_ID,
    )

    month_folder = find_or_create_folder(
        service,
        month_name,
        year_folder,
    )

    day_folder = find_or_create_folder(
        service,
        day_name,
        month_folder,
    )

    images_folder = find_or_create_folder(
        service,
        "IMAGENES",
        day_folder,
    )

    print()
    print("-" * 64)
    print(
        " SUBIENDO 6 TARJETAS"
    )
    print("-" * 64)
    print()

    uploaded = 0
    created = 0
    updated = 0
    missing = []

    for item in items:
        numero = item.get(
            "numero",
            "00",
        )

        titulo = item.get(
            "titulo",
            "noticia",
        )

        filename = (
            f"{numero}_"
            f"{slugify(titulo)[:50]}"
            f".png"
        )

        local_path = (
            OUTPUT_DIR
            / filename
        )

        if not local_path.exists():
            print(
                f"NO ENCONTRADA: {filename}"
            )

            missing.append(
                filename
            )

            continue

        _, status = upload_or_update_file(
            service,
            local_path,
            images_folder,
            numero,
        )

        uploaded += 1

        if status == "created":
            created += 1

        elif status == "updated":
            updated += 1

    folder_url = (
        "https://drive.google.com/drive/folders/"
        f"{images_folder}"
    )

    print()
    print("=" * 64)
    print(
        " PROCESO TERMINADO"
    )
    print("=" * 64)
    print()

    print(
        f"Imágenes procesadas: {uploaded}"
    )

    print(
        f"Nuevas: {created}"
    )

    print(
        f"Actualizadas: {updated}"
    )

    print(
        f"No encontradas: {len(missing)}"
    )

    print()

    print(
        "Estructura del día:"
    )

    print(
        f"{year_name}"
    )

    print(
        f"└── {month_name}"
    )

    print(
        f"    └── {day_name}"
    )

    print(
        "        └── IMAGENES"
    )

    print()

    print(
        "Carpeta del día:"
    )

    print(
        folder_url
    )

    print()

    if missing:
        print(
            "ERROR: faltaron archivos locales:"
        )

        for filename in missing:
            print(
                f"  - {filename}"
            )

        raise SystemExit(1)

    if uploaded != EXPECTED_COUNT:
        raise RuntimeError(
            f"Solo se procesaron {uploaded} de "
            f"{EXPECTED_COUNT} imágenes."
        )

    print(
        "✅ 6 tarjetas disponibles en Drive."
    )

    print()


if __name__ == "__main__":
    main()
