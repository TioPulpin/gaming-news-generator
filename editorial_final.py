import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from googlenewsdecoder import gnewsdecoder


# =========================================================
# RUTAS / CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "ai_config.json"
SHORTLIST_FILE = BASE_DIR / "data" / "shortlist.json"

PREVIEW_FILE = (
    BASE_DIR
    / "data"
    / "editorial_candidates.json"
)

NEWS_FILE = (
    BASE_DIR
    / "data"
    / "noticias.json"
)

ENV_FILE = BASE_DIR / ".env"

LIMA = ZoneInfo("America/Lima")

MODEL_NAME = "gpt-5.6-terra"

EXPECTED_CANDIDATES = 24
FINAL_COUNT = 6

MAX_OUTPUT_TOKENS = 3000

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    ),
    "Accept-Language": (
        "en-US,en;q=0.9,es;q=0.8"
    ),
}

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


# =========================================================
# PROMPT EDITORIAL
# =========================================================

INSTRUCTIONS = """
Eres el editor jefe de una cuenta de noticias en español enfocada en
VIDEOJUEGOS/GAMING, TECNOLOGÍA/IA y CULTURA POP.

Recibirás 24 candidatas:
- 8 de gaming
- 8 de tecnología
- 8 de cultura pop

Ya fueron filtradas gratuitamente por un sistema local.

Debes realizar DOS trabajos en ESTA MISMA RESPUESTA:

1. Elegir exactamente 6 noticias.
2. Redactar esas 6 noticias en español listas para tarjetas de redes.

========================================================
DISTRIBUCIÓN EDITORIAL
========================================================

OBJETIVO NORMAL:
- 2 Gaming
- 2 Tecnología
- 2 Cultura Pop

CALIDAD PRIMERO:
Si una rama realmente no tiene dos noticias suficientemente fuertes,
puedes redistribuir UN SOLO espacio.

Distribuciones permitidas:
- 2 / 2 / 2
- 3 / 2 / 1
- 3 / 1 / 2
- 2 / 3 / 1
- 1 / 3 / 2
- 2 / 1 / 3
- 1 / 2 / 3

REGLAS:
- mínimo 1 noticia por rama;
- máximo 3 noticias por rama;
- exactamente 6 noticias en total;
- no uses 4 o más noticias de una misma rama;
- no redistribuyas solo porque una tercera noticia sea ligeramente mejor:
  hazlo únicamente cuando una rama esté claramente floja.

========================================================
CRITERIOS GENERALES
========================================================

Prioriza:
- actualidad;
- importancia;
- consecuencia real;
- potencial informativo;
- capacidad de generar conversación;
- atractivo para Instagram, TikTok, Reels y Shorts;
- variedad temática;
- fuentes razonablemente confiables;
- hechos confirmados por encima de rumores.

Evita:
- duplicados;
- ofertas;
- guías;
- listicles;
- artículos evergreen;
- SEO vacío;
- contenido meramente promocional;
- rumores débiles;
- noticias empresariales demasiado nicho;
- trailers menores sin una novedad relevante.

========================================================
GAMING
========================================================

Prioriza:
- lanzamientos y fechas importantes;
- retrasos y cancelaciones;
- PlayStation, Xbox, Nintendo y PC;
- servicios como Game Pass y PlayStation Plus;
- estudios y publishers;
- adquisiciones, despidos, cierres;
- cambios de plataforma;
- hardware gaming;
- Riot, Valorant, League of Legends y esports cuando sean relevantes.

========================================================
TECNOLOGÍA / IA
========================================================

Prioriza:
- inteligencia artificial;
- OpenAI, Google, Microsoft, Anthropic;
- Apple, Samsung, Android, iOS;
- NVIDIA, AMD, Intel, chips y hardware;
- software importante;
- redes sociales y plataformas;
- ciberseguridad de impacto;
- regulación tecnológica relevante;
- grandes cambios de productos o servicios.

Evita dar demasiado peso a:
- funding de startups poco conocidas;
- bolsa o movimientos de acciones;
- B2B extremadamente nicho;
- explainers genéricos.

========================================================
CULTURA POP
========================================================

Prioriza:
- cine y series;
- Marvel, DC, Star Wars, Disney;
- Netflix, Max, Prime Video;
- anime y manga;
- renovaciones y cancelaciones;
- fechas de estreno;
- casting;
- trailers importantes;
- adaptaciones;
- anuncios de franquicias relevantes.

Evita:
- calendarios genéricos;
- listas de estrenos;
- recopilatorios;
- trailers de personajes o temas musicales menores;
- rumores sin respaldo.

========================================================
REDACCIÓN
========================================================

Todo debe quedar en español natural.

TITULAR:
- idealmente 6 a 14 palabras;
- periodístico;
- claro;
- atractivo;
- sin clickbait;
- no escribir todo en mayúsculas.

RESUMEN:
- aproximadamente 40 a 60 palabras;
- explica qué pasó;
- explica por qué importa;
- sin relleno.

DESTACADOS:
- tituloDestacado: 1 o 2 fragmentos LITERALES del titular.
- resumenDestacado: 1 o 2 fragmentos LITERALES del resumen.

EXTRAS:
- por_que_importa: una frase breve;
- anguloShort: una frase breve para convertirla en video corto.

IMPORTANTE:
- conserva candidate_id exactamente;
- conserva editorial_branch;
- no inventes URLs, fuentes, fechas ni hechos;
- la imagen NO se decide aquí;
- el sistema buscará imágenes reales de Internet después.
"""


# =========================================================
# STRUCTURED OUTPUT
# =========================================================

ITEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "candidate_id": {
            "type": "integer"
        },
        "editorial_branch": {
            "type": "string",
            "enum": [
                "gaming",
                "tecnologia",
                "cultura_pop",
            ],
        },
        "categoria": {
            "type": "string"
        },
        "titulo": {
            "type": "string"
        },
        "tituloDestacado": {
            "type": "array",
            "minItems": 1,
            "maxItems": 2,
            "items": {
                "type": "string"
            },
        },
        "resumen": {
            "type": "string"
        },
        "resumenDestacado": {
            "type": "array",
            "minItems": 1,
            "maxItems": 2,
            "items": {
                "type": "string"
            },
        },
        "por_que_importa": {
            "type": "string"
        },
        "anguloShort": {
            "type": "string"
        },
    },
    "required": [
        "candidate_id",
        "editorial_branch",
        "categoria",
        "titulo",
        "tituloDestacado",
        "resumen",
        "resumenDestacado",
        "por_que_importa",
        "anguloShort",
    ],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "noticias": {
            "type": "array",
            "minItems": FINAL_COUNT,
            "maxItems": FINAL_COUNT,
            "items": ITEM_SCHEMA,
        }
    },
    "required": [
        "noticias"
    ],
}


# =========================================================
# UTILIDADES
# =========================================================

def clean_text(text):
    return re.sub(
        r"\s+",
        " ",
        str(text or ""),
    ).strip()


def trim(text, limit):
    text = clean_text(text)

    if len(text) <= limit:
        return text

    return (
        text[:limit]
        .rsplit(
            " ",
            1,
        )[0]
        .strip()
        + "…"
    )


def is_google_news(url):
    text = str(
        url or ""
    )

    return (
        "news.google.com" in text
        or "/rss/articles/" in text
        or "/read/" in text
    )


def resolve_url(url):
    if not url:
        return ""

    if not is_google_news(
        url
    ):
        return url

    try:
        result = gnewsdecoder(
            url,
            interval=1,
        )

        if (
            isinstance(
                result,
                dict,
            )
            and result.get(
                "status"
            )
            and result.get(
                "decoded_url"
            )
        ):
            return result[
                "decoded_url"
            ]

    except Exception:
        pass

    return url


def extract_from_html(
    url,
    html,
):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    title = ""

    for attrs in (
        {
            "property": "og:title"
        },
        {
            "name": "twitter:title"
        },
    ):
        tag = soup.find(
            "meta",
            attrs=attrs,
        )

        if (
            tag
            and tag.get(
                "content"
            )
        ):
            title = clean_text(
                tag.get(
                    "content"
                )
            )
            break

    if not title:
        h1 = soup.find(
            "h1"
        )

        if h1:
            title = clean_text(
                h1.get_text(
                    " ",
                    strip=True,
                )
            )

    description = ""

    for attrs in (
        {
            "property": "og:description"
        },
        {
            "name": "description"
        },
        {
            "name": "twitter:description"
        },
    ):
        tag = soup.find(
            "meta",
            attrs=attrs,
        )

        if (
            tag
            and tag.get(
                "content"
            )
        ):
            description = clean_text(
                tag.get(
                    "content"
                )
            )
            break

    article = (
        soup.find(
            "article"
        )
        or soup.find(
            "main"
        )
        or soup
    )

    paragraphs = []

    for p in article.find_all(
        "p",
        limit=25,
    ):
        text = clean_text(
            p.get_text(
                " ",
                strip=True,
            )
        )

        if len(text) < 70:
            continue

        if text not in paragraphs:
            paragraphs.append(
                text
            )

        if len(paragraphs) >= 2:
            break

    return {
        "resolved_url": url,
        "page_title": trim(
            title,
            320,
        ),
        "description": trim(
            description,
            650,
        ),
        "extract": trim(
            " ".join(
                paragraphs
            ),
            1100,
        ),
    }


def fetch_requests(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=16,
        allow_redirects=True,
    )

    response.raise_for_status()

    return extract_from_html(
        response.url,
        response.text,
    )


def fetch_browser(url):
    from playwright.sync_api import (
        sync_playwright
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            viewport={
                "width": 1440,
                "height": 1000,
            },
            user_agent=HEADERS[
                "User-Agent"
            ],
            locale="en-US",
        )

        try:
            page.goto(
                url,
                wait_until=(
                    "domcontentloaded"
                ),
                timeout=22000,
            )

            page.wait_for_timeout(
                900
            )

            return extract_from_html(
                page.url,
                page.content(),
            )

        finally:
            browser.close()


def enrich_candidate(
    item,
    candidate_id,
):
    original_url = (
        item.get(
            "link"
        )
        or item.get(
            "url"
        )
        or ""
    )

    resolved_url = resolve_url(
        original_url
    )

    context = {
        "candidate_id": candidate_id,

        "editorial_branch": item.get(
            "editorial_branch",
            item.get(
                "category_internal",
                "",
            ),
        ),

        "branch_rank": item.get(
            "branch_rank",
            0,
        ),

        "editorial_score": item.get(
            "editorial_score",
            0,
        ),

        "title": trim(
            item.get(
                "title",
                "",
            ),
            320,
        ),

        "source": item.get(
            "source",
            "",
        ),

        "published": item.get(
            "published",
            "",
        ),

        "url": (
            resolved_url
            or original_url
        ),

        "page_title": "",
        "description": "",
        "extract": "",

        "context_status": (
            "RSS_ONLY"
        ),
    }

    if not resolved_url:
        return context

    try:
        extracted = fetch_requests(
            resolved_url
        )

        context.update(
            extracted
        )

        context[
            "context_status"
        ] = "REQUESTS"

        return context

    except Exception:
        pass

    try:
        extracted = fetch_browser(
            resolved_url
        )

        context.update(
            extracted
        )

        context[
            "context_status"
        ] = "BROWSER"

        return context

    except Exception:
        return context


def estimate_tokens(text):
    return max(
        int(
            len(
                str(
                    text or ""
                )
            )
            / 3.2
        )
        + 400,
        1,
    )


def card_date():
    now = datetime.now(
        LIMA
    )

    return (
        f"{now.day:02d} "
        f"{MONTHS_ES[now.month]} "
        f"{now.year}"
    )


def branch_label(branch):
    labels = {
        "gaming": "GAMING",
        "tecnologia": "TECNOLOGÍA",
        "cultura_pop": "CULTURA POP",
    }

    return labels.get(
        branch,
        branch.upper(),
    )


# =========================================================
# VALIDACIÓN EDITORIAL
# =========================================================

def validate_editorial_choice(
    chosen,
    candidate_map,
):
    if len(
        chosen
    ) != FINAL_COUNT:
        raise ValueError(
            "Terra no devolvió exactamente "
            "6 noticias."
        )

    ids = [
        item[
            "candidate_id"
        ]
        for item in chosen
    ]

    if len(
        set(
            ids
        )
    ) != FINAL_COUNT:
        raise ValueError(
            "Terra devolvió candidate_id "
            "duplicados."
        )

    for item in chosen:
        candidate_id = item[
            "candidate_id"
        ]

        if candidate_id not in candidate_map:
            raise ValueError(
                "candidate_id inexistente: "
                f"{candidate_id}"
            )

        expected_branch = (
            candidate_map[
                candidate_id
            ][
                "editorial_branch"
            ]
        )

        returned_branch = item[
            "editorial_branch"
        ]

        if (
            returned_branch
            != expected_branch
        ):
            raise ValueError(
                "Terra cambió la rama de "
                f"candidate_id {candidate_id}: "
                f"{expected_branch} -> "
                f"{returned_branch}"
            )

    counts = Counter(
        item[
            "editorial_branch"
        ]
        for item in chosen
    )

    for branch in (
        "gaming",
        "tecnologia",
        "cultura_pop",
    ):
        count = counts.get(
            branch,
            0,
        )

        if (
            count < 1
            or count > 3
        ):
            raise ValueError(
                "Distribución editorial inválida: "
                f"{dict(counts)}"
            )

    return counts


# =========================================================
# MAIN
# =========================================================

def main():
    config = json.loads(
        CONFIG_FILE.read_text(
            encoding="utf-8"
        )
    )

    api_enabled = bool(
        config.get(
            "api_enabled",
            False,
        )
    )

    shortlist = json.loads(
        SHORTLIST_FILE.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        shortlist,
        list,
    ):
        raise ValueError(
            "shortlist.json no es una lista."
        )

    print()
    print("=" * 64)
    print(
        " EDITORIAL FINAL V2.1 - "
        "GAMING + TECNOLOGÍA + CULTURA POP"
    )
    print("=" * 64)
    print()

    print(
        "Candidatas recibidas:",
        len(
            shortlist
        )
    )

    if (
        len(
            shortlist
        )
        != EXPECTED_CANDIDATES
    ):
        print(
            "ADVERTENCIA: se esperaban "
            f"{EXPECTED_CANDIDATES} candidatas."
        )

    print()

    candidates = []

    for index, item in enumerate(
        shortlist,
        start=1,
    ):
        branch = item.get(
            "editorial_branch",
            "",
        )

        print(
            f"{index:02d}. "
            f"[{branch_label(branch)}] "
            f"{trim(item.get('title', ''), 68)}"
        )

        enriched = enrich_candidate(
            item,
            index,
        )

        candidates.append(
            enriched
        )

        print(
            "    Contexto:",
            enriched[
                "context_status"
            ]
        )

    PREVIEW_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    PREVIEW_FILE.write_text(
        json.dumps(
            candidates,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    input_text = json.dumps(
        candidates,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    )

    estimated_input_tokens = (
        estimate_tokens(
            INSTRUCTIONS
            + input_text
        )
    )

    current_counts = Counter(
        item[
            "editorial_branch"
        ]
        for item in candidates
    )

    print()
    print("=" * 64)
    print(" PREPARACIÓN TERRA")
    print("=" * 64)
    print()

    print(
        "Gaming preparado:",
        current_counts.get(
            "gaming",
            0,
        ),
    )

    print(
        "Tecnología preparada:",
        current_counts.get(
            "tecnologia",
            0,
        ),
    )

    print(
        "Cultura Pop preparada:",
        current_counts.get(
            "cultura_pop",
            0,
        ),
    )

    print()

    print(
        "Modelo:",
        MODEL_NAME
    )

    print(
        "Una sola llamada pagada: SÍ"
    )

    print(
        "Búsqueda web OpenAI: NO"
    )

    print(
        "Imágenes IA: NO"
    )

    print(
        "Objetivo final: "
        "6 noticias"
    )

    print(
        "Distribución objetivo: "
        "2 + 2 + 2"
    )

    print(
        "Fallback permitido: "
        "3 + 2 + 1"
    )

    print(
        "Tokens entrada estimados:",
        estimated_input_tokens
    )

    print(
        "Máximo salida:",
        MAX_OUTPUT_TOKENS
    )

    print()

    # =====================================================
    # DRY RUN
    # =====================================================

    if not api_enabled:
        print(
            "API habilitada: False"
        )

        print(
            "✅ 24 candidatas preparadas."
        )

        print(
            "✅ Contexto web obtenido "
            "sin OpenAI API."
        )

        print(
            "✅ Terra NO fue llamado."
        )

        print(
            "✅ Costo API: $0.00"
        )

        print()
        print(
            "Vista previa:"
        )

        print(
            PREVIEW_FILE
        )

        print()

        return

    # =====================================================
    # API ACTIVA
    # =====================================================

    from openai import OpenAI

    from api_budget import (
        assert_budget_for_call,
        budget_status,
        register_text_usage,
    )

    load_dotenv(
        ENV_FILE,
        override=True,
    )

    api_key = os.getenv(
        "OPENAI_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY no está "
            "configurada en .env."
        )

    print(
        "API key cargada desde .env: SÍ"
    )

    precheck = assert_budget_for_call(
        model=MODEL_NAME,
        estimated_input_tokens=(
            estimated_input_tokens
        ),
        max_output_tokens=(
            MAX_OUTPUT_TOKENS
        ),
        safety_margin_usd=0.01,
    )

    print(
        "Gasto mensual actual:",
        f'${precheck["spent"]:.4f}'
    )

    print(
        "Reserva conservadora:",
        f'${precheck["estimated_max_call_cost"]:.4f}'
    )

    print(
        "Proyección máxima:",
        f'${precheck["projected_after_call"]:.4f}'
    )

    print(
        "STOP interno:",
        f'${precheck["stop"]:.2f}'
    )

    print()

    client = OpenAI(
        api_key=api_key
    )

    response = client.responses.create(
        model=MODEL_NAME,

        reasoning={
            "effort": "low"
        },

        store=False,

        max_output_tokens=(
            MAX_OUTPUT_TOKENS
        ),

        instructions=(
            INSTRUCTIONS
        ),

        input=input_text,

        text={
            "format": {
                "type": "json_schema",
                "name": (
                    "multitema_news_final_es"
                ),
                "strict": True,
                "schema": OUTPUT_SCHEMA,
            }
        },
    )

    usage = response.usage

    if usage is None:
        raise RuntimeError(
            "La API no devolvió "
            "información de uso."
        )

    details = getattr(
        usage,
        "input_tokens_details",
        None,
    )

    cached_tokens = 0

    if details is not None:
        cached_tokens = int(
            getattr(
                details,
                "cached_tokens",
                0,
            )
            or 0
        )

    call_cost = register_text_usage(
        model=MODEL_NAME,
        input_tokens=int(
            usage.input_tokens
        ),
        output_tokens=int(
            usage.output_tokens
        ),
        cached_tokens=(
            cached_tokens
        ),
        label=(
            "TOP 6 multitemático + "
            "redacción en español"
        ),
    )

    editorial = json.loads(
        response.output_text
    )

    chosen = editorial[
        "noticias"
    ]

    candidate_map = {
        item[
            "candidate_id"
        ]: item
        for item in candidates
    }

    final_counts = (
        validate_editorial_choice(
            chosen,
            candidate_map,
        )
    )

    # =====================================================
    # CONSTRUIR noticias.json
    # =====================================================

    final_news = []

    for index, edited in enumerate(
        chosen,
        start=1,
    ):
        candidate_id = edited[
            "candidate_id"
        ]

        source = candidate_map[
            candidate_id
        ]

        branch = edited[
            "editorial_branch"
        ]

        final_news.append({
            "numero": (
                f"{index:02d}"
            ),

            "categoria": edited.get(
                "categoria"
            )
            or branch_label(
                branch
            ),

            "rama": branch,

            "fecha": card_date(),

            "titulo": edited[
                "titulo"
            ],

            "tituloDestacado": edited[
                "tituloDestacado"
            ],

            "resumen": edited[
                "resumen"
            ],

            "resumenDestacado": edited[
                "resumenDestacado"
            ],

            "imagen": "",

            "fuente": source[
                "source"
            ],

            "url": source[
                "url"
            ],

            "fecha_original": source[
                "published"
            ],

            "por_que_importa": edited[
                "por_que_importa"
            ],

            "anguloShort": edited[
                "anguloShort"
            ],

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

    status = budget_status()

    # =====================================================
    # RESULTADO
    # =====================================================

    print()
    print("=" * 64)
    print(" TOP 6 FINAL")
    print("=" * 64)
    print()

    for item in final_news:
        print(
            f'{item["numero"]}. '
            f'[{branch_label(item["rama"])}] '
            f'{item["titulo"]}'
        )

        print(
            "    Fuente:",
            item[
                "fuente"
            ]
        )

        print()

    print(
        "Distribución:"
    )

    print(
        "  Gaming:",
        final_counts.get(
            "gaming",
            0,
        )
    )

    print(
        "  Tecnología:",
        final_counts.get(
            "tecnologia",
            0,
        )
    )

    print(
        "  Cultura Pop:",
        final_counts.get(
            "cultura_pop",
            0,
        )
    )

    print()

    print("=" * 64)
    print(" COSTO")
    print("=" * 64)
    print()

    print(
        "Costo de esta ejecución:",
        f"${call_cost:.6f}"
    )

    print(
        "Acumulado del mes:",
        f'${status["spent"]:.4f}'
    )

    print(
        "STOP interno:",
        f'${status["stop"]:.2f}'
    )

    print()

    print(
        "✅ data/noticias.json "
        "quedó listo con 6 noticias."
    )

    print()


if __name__ == "__main__":
    main()
