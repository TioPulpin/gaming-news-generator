import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent

SHORTLIST_FILE = (
    BASE_DIR / "data" / "shortlist.json"
)

NEWS_FILE = (
    BASE_DIR / "data" / "noticias.json"
)

BACKUP_FILE = (
    BASE_DIR / "data" / "noticias_before_real_test.json"
)

LIMA = ZoneInfo("America/Lima")


MONTHS_ES = {
    1: "ENE",
    2: "FEB",
    3: "MAR",
    4: "ABR",
    5: "MAY",
    6: "JUN",
    7: "JUL",
    8: "AGO",
    9: "SEP",
    10: "OCT",
    11: "NOV",
    12: "DIC"
}


def clean_title(title):

    # Google News suele añadir " - Medio" al final.
    # Lo retiramos si coincide con la fuente más adelante,
    # pero aquí hacemos una limpieza sencilla.
    return (
        title
        .strip()
    )


if NEWS_FILE.exists():

    BACKUP_FILE.write_text(
        NEWS_FILE.read_text(
            encoding="utf-8"
        ),
        encoding="utf-8"
    )


shortlist = json.loads(
    SHORTLIST_FILE.read_text(
        encoding="utf-8"
    )
)


# Para la prueba usamos las 5 primeras.
selected = shortlist[:5]


now = datetime.now(
    LIMA
)

fecha_tarjeta = (
    f"{now.day:02d} "
    f"{MONTHS_ES[now.month]} "
    f"{now.year}"
)


news = []


for index, item in enumerate(
    selected,
    start=1
):

    original_title = clean_title(
        item.get(
            "title",
            ""
        )
    )

    source = item.get(
        "source",
        ""
    )

    # Para esta prueba usamos el titular original.
    # Después Terra lo redactará en español.
    title = original_title.upper()

    news.append({

        "numero": f"{index:02d}",

        "categoria": "GAMING",

        "fecha": fecha_tarjeta,

        "titulo": title,

        "tituloDestacado": [],

        "resumen": (
            "Tarjeta de prueba generada a partir "
            "de una noticia real encontrada por "
            "Gaming News Generator. El contenido "
            "editorial definitivo será redactado "
            "automáticamente en una fase posterior."
        ),

        "resumenDestacado": [],

        "imagen": "",

        "fuente": source,

        "url": item.get(
            "link",
            ""
        ),

        "fecha_original": item.get(
            "published",
            ""
        ),

        "imagenFuente": "",

        "imagenFuenteUrl": "",

        "imagenTipo": ""
    })


NEWS_FILE.write_text(

    json.dumps(
        news,
        ensure_ascii=False,
        indent=2
    ),

    encoding="utf-8"
)


print()
print("=" * 60)
print(" 5 NOTICIAS REALES PREPARADAS")
print("=" * 60)
print()


for item in news:

    print(
        item["numero"],
        "-",
        item["titulo"]
    )

    print(
        "   Fuente:",
        item["fuente"]
    )

    print(
        "   URL:",
        item["url"]
    )

    print()


print(
    "✅ noticias.json actualizado."
)

print(
    "✅ Se creó copia de seguridad."
)

print(
    "✅ Costo API: $0.00"
)

print()