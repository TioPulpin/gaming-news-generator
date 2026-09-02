import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent

CANDIDATES_FILE = (
    BASE_DIR
    / "data"
    / "editorial_candidates.json"
)

NEWS_FILE = (
    BASE_DIR
    / "data"
    / "noticias.json"
)

BACKUP_FILE = (
    BASE_DIR
    / "data"
    / "noticias_before_multitema_test.json"
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
    12: "DIC",
}

BRANCH_LABELS = {
    "gaming": "GAMING",
    "tecnologia": "TECNOLOGÍA",
    "cultura_pop": "CULTURA POP",
}


def clean_text(text):
    return " ".join(
        str(text or "").split()
    ).strip()


def trim_words(text, max_chars):
    text = clean_text(text)

    if len(text) <= max_chars:
        return text

    shortened = (
        text[:max_chars]
        .rsplit(" ", 1)[0]
        .strip()
    )

    return shortened + "…"


def literal_fragment(text, word_count):
    words = clean_text(text).split()

    if not words:
        return ""

    return " ".join(
        words[:word_count]
    )


def card_date():
    now = datetime.now(LIMA)

    return (
        f"{now.day:02d} "
        f"{MONTHS_ES[now.month]} "
        f"{now.year}"
    )


def choose_two_per_branch(candidates):
    selected = []

    for branch in (
        "gaming",
        "tecnologia",
        "cultura_pop",
    ):
        branch_items = [
            item
            for item in candidates
            if item.get("editorial_branch") == branch
        ]

        if len(branch_items) < 2:
            raise ValueError(
                f"No hay al menos 2 candidatas "
                f"para la rama {branch}."
            )

        selected.extend(
            branch_items[:2]
        )

    return selected


def build_summary(item, branch):
    text = (
        item.get("description")
        or item.get("extract")
        or ""
    )

    text = trim_words(
        text,
        360,
    )

    if text:
        return text

    fallbacks = {
        "gaming": (
            "Noticia seleccionada para comprobar el flujo "
            "de imágenes, tarjetas y publicación del sistema."
        ),
        "tecnologia": (
            "Noticia tecnológica seleccionada para comprobar "
            "el flujo completo de generación de tarjetas."
        ),
        "cultura_pop": (
            "Noticia de cultura pop seleccionada para comprobar "
            "el flujo completo de generación de tarjetas."
        ),
    }

    return fallbacks[branch]


def main():
    if not CANDIDATES_FILE.exists():
        raise FileNotFoundError(
            "No existe data/editorial_candidates.json. "
            "Ejecuta primero editorial_final.py con la API apagada."
        )

    candidates = json.loads(
        CANDIDATES_FILE.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(candidates, list):
        raise ValueError(
            "editorial_candidates.json debe ser una lista."
        )

    selected = choose_two_per_branch(
        candidates
    )

    if NEWS_FILE.exists():
        shutil.copy2(
            NEWS_FILE,
            BACKUP_FILE,
        )

    final_news = []

    for index, item in enumerate(
        selected,
        start=1,
    ):
        branch = item[
            "editorial_branch"
        ]

        title = trim_words(
            item.get(
                "page_title"
            )
            or item.get(
                "title"
            )
            or "Noticia de prueba",
            150,
        )

        summary = build_summary(
            item,
            branch,
        )

        title_highlight = literal_fragment(
            title,
            3,
        )

        summary_highlight = literal_fragment(
            summary,
            5,
        )

        final_news.append({
            "numero": f"{index:02d}",
            "categoria": BRANCH_LABELS[branch],
            "rama": branch,
            "fecha": card_date(),

            "titulo": title,
            "tituloDestacado": [
                title_highlight
            ],

            "resumen": summary,
            "resumenDestacado": [
                summary_highlight
            ],

            "imagen": "",

            "fuente": item.get(
                "source",
                "Sin fuente",
            ),

            "url": (
                item.get("resolved_url")
                or item.get("url")
                or ""
            ),

            "fecha_original": item.get(
                "published",
                "",
            ),

            "por_que_importa": (
                "Registro temporal para validar "
                "el flujo multitemático de seis tarjetas."
            ),

            "anguloShort": (
                "Prueba técnica del pipeline multitemático."
            ),

            "imagenFuente": "",
            "imagenFuenteUrl": "",
            "imagenTipo": "",
        })

    NEWS_FILE.write_text(
        json.dumps(
            final_news,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 64)
    print(
        " PRUEBA GRATUITA - "
        "6 NOTICIAS MULTITEMÁTICAS"
    )
    print("=" * 64)
    print()

    if BACKUP_FILE.exists():
        print(
            "Backup anterior:"
        )
        print(
            BACKUP_FILE
        )
        print()

    print(
        "Nuevo noticias.json:"
    )
    print(
        NEWS_FILE
    )
    print()

    for item in final_news:
        print(
            f'{item["numero"]}. '
            f'[{item["categoria"]}] '
            f'{item["titulo"]}'
        )

    print()
    print(
        "Distribución: "
        "2 Gaming + 2 Tecnología + 2 Cultura Pop"
    )
    print(
        "Costo OpenAI API: $0.00"
    )
    print()


if __name__ == "__main__":
    main()
