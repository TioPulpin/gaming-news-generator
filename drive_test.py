from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive.file"
]

FOLDER_MIME = "application/vnd.google-apps.folder"


# =========================================================
# AUTENTICACIÓN
# =========================================================

def get_credentials():

    creds = None

    if TOKEN_FILE.exists():

        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:

            creds.refresh(Request())

        else:

            if not CREDENTIALS_FILE.exists():

                raise FileNotFoundError(
                    "No se encontró credentials.json"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        TOKEN_FILE.write_text(
            creds.to_json(),
            encoding="utf-8"
        )

    return creds


# =========================================================
# UTILIDADES DE DRIVE
# =========================================================

def escape_query(text):

    return (
        text
        .replace("\\", "\\\\")
        .replace("'", "\\'")
    )


def find_folder(service, name, parent_id=None):

    safe_name = escape_query(name)

    query = (
        f"name='{safe_name}' "
        f"and mimeType='{FOLDER_MIME}' "
        f"and trashed=false"
    )

    if parent_id:

        query += f" and '{parent_id}' in parents"

    result = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name)"
    ).execute()

    folders = result.get(
        "files",
        []
    )

    if folders:

        return folders[0]["id"]

    return None


def create_folder(service, name, parent_id=None):

    metadata = {
        "name": name,
        "mimeType": FOLDER_MIME
    }

    if parent_id:

        metadata["parents"] = [
            parent_id
        ]

    folder = service.files().create(
        body=metadata,
        fields="id, name"
    ).execute()

    print(
        f"Carpeta creada: {name}"
    )

    return folder["id"]


def find_or_create_folder(
    service,
    name,
    parent_id=None
):

    folder_id = find_folder(
        service,
        name,
        parent_id
    )

    if folder_id:

        print(
            f"Carpeta encontrada: {name}"
        )

        return folder_id

    return create_folder(
        service,
        name,
        parent_id
    )


# =========================================================
# PROGRAMA PRINCIPAL
# =========================================================

print()
print("==========================================")
print(" GAMING NEWS GENERATOR - GOOGLE DRIVE")
print("==========================================")
print()

credentials = get_credentials()

service = build(
    "drive",
    "v3",
    credentials=credentials,
    cache_discovery=False
)


# Carpeta principal

nicolas_folder = find_or_create_folder(
    service,
    "Nicolas Hernandez"
)


# Carpeta de noticias

news_folder = find_or_create_folder(
    service,
    "Noticias Gaming",
    nicolas_folder
)


print()
print("==========================================")
print(" DRIVE CONECTADO CORRECTAMENTE")
print("==========================================")
print()

print(
    "Carpeta:"
)

print(
    f"https://drive.google.com/drive/folders/{news_folder}"
)

print()