import json
import time
from collections import Counter
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import feedparser
import requests


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_FILE = BASE_DIR / "data" / "candidates.json"

LIMA = ZoneInfo("America/Lima")

PRIMARY_WINDOW_DAYS = 3
FALLBACK_WINDOW_DAYS = 7

# Solo se amplía a 7 días si una rama queda excepcionalmente pobre.
MIN_BRANCH_CANDIDATES = 45

REQUEST_TIMEOUT = 18
REQUEST_PAUSE_SECONDS = 0.20

GOOGLE_NEWS_BASE = (
    "https://news.google.com/rss/search"
    "?q={query}"
    "&hl=en-US"
    "&gl=US"
    "&ceid=US:en"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    )
}


# =========================================================
# RAMAS EDITORIALES
# =========================================================

# IMPORTANTE:
# - Estas búsquedas solo DESCUBREN noticias.
# - El ranking posterior decidirá cuáles merecen competir.
# - Terra no se usa aquí.
#
# La intención es que la cuenta tenga tres pilares:
# 1) Gaming / videojuegos
# 2) Tecnología / IA
# 3) Cultura Pop

QUERY_GROUPS = {
    "gaming": [
        "video game industry",
        "PlayStation Xbox Nintendo gaming",
        "PC gaming Steam Valve",
        "video game studio layoffs acquisition",
        "gaming publisher industry",
        "video game announcement release delay",
        "Riot Games Valorant League of Legends esports",
        "gaming hardware console GPU",
        "Game Pass PlayStation Plus Nintendo Switch Online",
        "Capcom Konami Ubisoft EA Sega Square Enix gaming",
    ],

    "tecnologia": [
        "technology industry artificial intelligence",
        "OpenAI Google Gemini Anthropic Microsoft AI",
        "Apple iPhone iOS Mac technology",
        "Samsung Android smartphone technology",
        "Nvidia AMD Intel GPU CPU chips",
        "Microsoft Windows software technology",
        "cybersecurity data breach technology",
        "Meta Instagram TikTok social media technology",
        "consumer electronics gadgets hardware",
        "AI tools software launch update",
    ],

    "cultura_pop": [
        "pop culture entertainment movies TV streaming",
        "Marvel DC superhero movie series",
        "Star Wars Disney entertainment",
        "Netflix HBO Max Prime Video streaming series",
        "anime manga Crunchyroll entertainment",
        "movie trailer casting release date",
        "TV series renewal cancellation streaming",
        "video game adaptation movie TV series",
        "Disney Pixar animation movie",
        "anime movie series announcement",
    ],
}


# =========================================================
# UTILIDADES
# =========================================================

def google_news_url(query, days):
    final_query = f"{query} when:{days}d"

    return GOOGLE_NEWS_BASE.format(
        query=quote_plus(final_query)
    )


def parse_published(entry):
    raw = (
        entry.get("published")
        or entry.get("updated")
        or ""
    )

    if not raw:
        return None

    try:
        date = parsedate_to_datetime(raw)

        if date.tzinfo is None:
            date = date.replace(
                tzinfo=ZoneInfo("UTC")
            )

        return date.astimezone(LIMA)

    except Exception:
        return None


def get_source(entry):
    source = entry.get("source")

    if isinstance(source, dict):
        title = source.get("title")

        if title:
            return str(title).strip()

    # Google News suele añadir " - Medio" al final.
    title = str(
        entry.get("title", "")
    ).strip()

    if " - " in title:
        return title.rsplit(
            " - ",
            1
        )[-1].strip()

    return "Sin fuente"


def strip_source_from_title(title, source):
    title = str(
        title or ""
    ).strip()

    source = str(
        source or ""
    ).strip()

    suffix = f" - {source}"

    if (
        source
        and title.lower().endswith(
            suffix.lower()
        )
    ):
        return title[
            :-len(suffix)
        ].strip()

    return title


def canonical_key(item):
    # Google News puede entregar el mismo enlace desde varias consultas.
    link = str(
        item.get("link", "")
    ).strip()

    if link:
        return "url:" + link

    title = str(
        item.get("title", "")
    ).lower().strip()

    source = str(
        item.get("source", "")
    ).lower().strip()

    return f"title:{title}|source:{source}"


# =========================================================
# DESCARGA RSS
# =========================================================

def fetch_query(
    editorial_branch,
    query,
    days,
):
    url = google_news_url(
        query,
        days
    )

    print(
        f"Buscando [{editorial_branch.upper()}]: "
        f"{query} when:{days}d"
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except Exception as exc:
        print(
            f"  ERROR RSS: {exc}"
        )
        return []

    feed = feedparser.parse(
        response.content
    )

    print(
        f"  Encontradas: {len(feed.entries)}"
    )

    now = datetime.now(LIMA)

    oldest_allowed = now - timedelta(
        days=days,
        hours=2,
    )

    results = []

    for entry in feed.entries:
        published = parse_published(
            entry
        )

        if (
            published is not None
            and published < oldest_allowed
        ):
            continue

        source = get_source(
            entry
        )

        raw_title = str(
            entry.get(
                "title",
                ""
            )
        ).strip()

        title = strip_source_from_title(
            raw_title,
            source,
        )

        link = str(
            entry.get(
                "link",
                ""
            )
        ).strip()

        if not title:
            continue

        results.append({
            "title": title,
            "source": source,
            "published": (
                published.isoformat()
                if published
                else ""
            ),
            "link": link,

            # NUEVO: rama desde la que fue descubierta.
            "category_internal": editorial_branch,

            # Si la misma noticia aparece en otra rama,
            # se fusionará aquí.
            "categories_seen": [
                editorial_branch
            ],

            "search_query": query,

            "discovery_window_days": days,
        })

    return results


# =========================================================
# FUSIÓN DE DUPLICADOS ENTRE CONSULTAS
# =========================================================

def merge_items(items):
    merged = {}

    for item in items:
        key = canonical_key(
            item
        )

        if key not in merged:
            merged[key] = dict(
                item
            )
            continue

        existing = merged[key]

        categories = set(
            existing.get(
                "categories_seen",
                []
            )
        )

        categories.update(
            item.get(
                "categories_seen",
                []
            )
        )

        existing[
            "categories_seen"
        ] = sorted(
            categories
        )

        # Conservamos la ventana más fresca.
        existing[
            "discovery_window_days"
        ] = min(
            int(
                existing.get(
                    "discovery_window_days",
                    FALLBACK_WINDOW_DAYS,
                )
            ),
            int(
                item.get(
                    "discovery_window_days",
                    FALLBACK_WINDOW_DAYS,
                )
            ),
        )

        # Si faltaba fecha y el duplicado sí tiene una,
        # aprovechamos la información.
        if (
            not existing.get(
                "published"
            )
            and item.get(
                "published"
            )
        ):
            existing[
                "published"
            ] = item[
                "published"
            ]

    return list(
        merged.values()
    )


# =========================================================
# EJECUTAR UNA RAMA
# =========================================================

def fetch_branch(
    branch,
    queries,
):
    branch_items = []

    for query in queries:
        branch_items.extend(
            fetch_query(
                branch,
                query,
                PRIMARY_WINDOW_DAYS,
            )
        )

        time.sleep(
            REQUEST_PAUSE_SECONDS
        )

    branch_unique = merge_items(
        branch_items
    )

    # Fallback 7 días:
    # únicamente si una rama queda realmente pobre.
    if (
        len(branch_unique)
        < MIN_BRANCH_CANDIDATES
    ):
        print()
        print(
            f"⚠ {branch.upper()} tiene solo "
            f"{len(branch_unique)} candidatas."
        )

        print(
            f"  Ampliando esa rama hasta "
            f"{FALLBACK_WINDOW_DAYS} días..."
        )

        for query in queries:
            branch_items.extend(
                fetch_query(
                    branch,
                    query,
                    FALLBACK_WINDOW_DAYS,
                )
            )

            time.sleep(
                REQUEST_PAUSE_SECONDS
            )

        branch_unique = merge_items(
            branch_items
        )

    return branch_unique


# =========================================================
# MAIN
# =========================================================

def main():
    print()
    print("=" * 60)
    print(" GAMING NEWS GENERATOR - INVESTIGACIÓN MULTITEMÁTICA V2")
    print("=" * 60)
    print()

    all_items = []

    branch_counts_before_global_merge = {}

    for branch, queries in QUERY_GROUPS.items():
        print()
        print("-" * 60)
        print(
            f" RAMA: {branch.upper()}"
        )
        print("-" * 60)
        print()

        branch_items = fetch_branch(
            branch,
            queries,
        )

        branch_counts_before_global_merge[
            branch
        ] = len(
            branch_items
        )

        all_items.extend(
            branch_items
        )

        print()
        print(
            f"Candidatas únicas de "
            f"{branch.upper()}: "
            f"{len(branch_items)}"
        )

    # Deduplicación global.
    # Si una noticia apareció, por ejemplo, en GAMING y TECNOLOGÍA,
    # se conserva una sola vez y categories_seen tendrá ambas.
    candidates = merge_items(
        all_items
    )

    # Ordenar por fecha, más reciente primero.
    def date_sort_key(item):
        value = item.get(
            "published",
            ""
        )

        try:
            return datetime.fromisoformat(
                value
            )
        except Exception:
            return datetime.min.replace(
                tzinfo=LIMA
            )

    candidates.sort(
        key=date_sort_key,
        reverse=True,
    )

    # IDs estables para el archivo de investigación.
    for index, item in enumerate(
        candidates,
        start=1,
    ):
        item[
            "candidate_id"
        ] = index

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            candidates,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    category_counter = Counter()

    for item in candidates:
        for category in item.get(
            "categories_seen",
            []
        ):
            category_counter[
                category
            ] += 1

    print()
    print("=" * 60)
    print(" RESULTADO")
    print("=" * 60)
    print()

    print(
        f"Candidatas únicas globales: "
        f"{len(candidates)}"
    )

    print()

    print(
        "Descubrimientos por rama "
        "(una noticia puede aparecer en más de una):"
    )

    for branch in QUERY_GROUPS:
        print(
            f"  {branch.upper():12} "
            f"{category_counter[branch]}"
        )

    print()
    print(
        "Archivo generado:"
    )
    print(
        OUTPUT_FILE
    )

    print()
    print(
        "Primeras 18 candidatas:"
    )
    print()

    for item in candidates[:18]:
        categories = "/".join(
            category.upper()
            for category in item.get(
                "categories_seen",
                []
            )
        )

        print(
            f'{item["candidate_id"]:02d}. '
            f'[{categories}] '
            f'{item["title"]}'
        )

        print(
            f'    Fuente: '
            f'{item["source"]}'
        )

        print(
            f'    Fecha: '
            f'{item["published"]}'
        )

        print()

    print(
        "Costo OpenAI API: $0.00"
    )

    print()


if __name__ == "__main__":
    main()
