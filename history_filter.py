from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from rapidfuzz import fuzz


BASE_DIR = Path(__file__).resolve().parent

CANDIDATES_FILE = BASE_DIR / "data" / "candidates.json"
HISTORY_FILE = BASE_DIR / "data" / "published_history.json"
BLOCKED_FILE = BASE_DIR / "data" / "blocked_duplicates.json"

BLOCK_DAYS = 10


STOPWORDS = {
    # Español
    "de", "del", "la", "las", "el", "los",
    "un", "una", "unos", "unas",
    "y", "o", "en", "por", "para", "con",
    "sin", "sobre", "su", "sus",
    "que", "se", "a", "al", "como",
    "mas", "ya", "este", "esta",
    "desde", "hasta", "tras",

    # Inglés
    "the", "a", "an", "and", "or", "of",
    "in", "on", "for", "to", "with",
    "without", "from", "by", "its",
    "is", "are", "will", "this", "that",
    "as", "at", "into", "after", "before",

    # Editoriales
    "new", "nuevo", "nueva",
    "official", "oficial",
    "first", "primer", "primera",
    "more", "details", "everything",
    "ahead", "live",
}


# Plataformas o términos demasiado amplios.
# No sirven por sí solos para afirmar que dos noticias
# hablan de la misma historia.
GENERIC_SUBJECT_TOKENS = {

    # V4_GENERIC_TIME_TOKENS
    # Fechas, temporadas y palabras demasiado genericas.
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre",
    "noviembre", "diciembre",

    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october",
    "november", "december",

    "temporada", "temporadas",
    "season", "seasons",

    "primera", "primer",
    "segunda", "segundo",
    "tercera", "tercer",

    "first", "second", "third",

    "fecha", "fechas",
    "date", "dates",


    "nintendo",
    "switch",
    "playstation",
    "xbox",
    "console",
    "consoles",
    "consola",
    "consolas",
    "gaming",
    "game",
    "games",
    "juego",
    "juegos",
    "studio",
    "studios",
    "company",
    "windows",
    "android",
    "ios",
    "pc",
    "anime",
    "entertainment",
    "news",
    "video",
    "version",
}


# Solo estos eventos justifican automáticamente
# volver a cubrir un tema dentro de los 5 días.
#
# "trailer" y "launch" NO están aquí a propósito:
# muchas veces forman parte del mismo anuncio original.
MATERIAL_NEW_EVENTS = {
    "delay",
    "cancel",
    "sales",
    "acquisition",
    "gameplay",
    "beta",
    "demo",
}


ALL_EVENTS = {
    "delay",
    "launch",
    "release",
    "announce",
    "movie",
    "trailer",
    "invest",
    "breach",
    "stolen",
    "dub",
    "weekly",
    "cancel",
    "sales",
    "acquisition",
    "gameplay",
    "beta",
    "demo",
}


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        str(text or ""),
    )

    return "".join(
        ch
        for ch in normalized
        if not unicodedata.combining(ch)
    )


def normalize_text(text: str) -> str:
    text = remove_accents(
        str(text or "").lower()
    )

    text = re.sub(
        r"https?://\S+",
        " ",
        text,
    )

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def is_year(token: str) -> bool:
    if not token.isdigit():
        return False

    try:
        value = int(token)
    except ValueError:
        return False

    return 2000 <= value <= 2099


def canonical_event(token: str) -> str:
    token = normalize_text(token)

    if not token:
        return ""

    if (
        token.startswith("delay")
        or token.startswith("retras")
        or token.startswith("aplaz")
        or token.startswith("postpon")
    ):
        return "delay"

    if (
        token.startswith("cancel")
    ):
        return "cancel"

    if token in {
        "launch",
        "launched",
        "estreno",
        "estrena",
    }:
        return "launch"

    if (
        token.startswith("release")
        or token.startswith("lanz")
        or token.startswith("coming")
        or token.startswith("llega")
    ):
        return "release"

    if (
        token.startswith("announ")
        or token.startswith("anunci")
        or token.startswith("confirm")
        or token.startswith("reveal")
        or token.startswith("unveil")
    ):
        return "announce"

    if token in {
        "movie",
        "film",
        "pelicula",
    }:
        return "movie"

    if token in {
        "trailer",
        "teaser",
    }:
        return "trailer"

    if (
        token.startswith("invest")
        or token.startswith("inviert")
        or token.startswith("invers")
    ):
        return "invest"

    if (
        token.startswith("breach")
        or token.startswith("cyberattack")
        or token.startswith("ciberata")
    ):
        return "breach"

    if (
        token.startswith("stol")
        or token.startswith("rob")
    ):
        return "stolen"

    if (
        token.startswith("dub")
        or token.startswith("simuldub")
        or token.startswith("dobl")
    ):
        return "dub"

    if (
        token.startswith("week")
        or token.startswith("seman")
    ):
        return "weekly"

    if (
        token.startswith("sales")
        or token.startswith("sold")
        or token.startswith("venta")
    ):
        return "sales"

    if (
        token.startswith("acqui")
        or token.startswith("adquis")
    ):
        return "acquisition"

    if token == "gameplay":
        return "gameplay"

    if token == "beta":
        return "beta"

    if token == "demo":
        return "demo"

    return ""


def get_events(text: str) -> set[str]:
    result = set()

    for token in normalize_text(text).split():
        event = canonical_event(token)

        if event:
            result.add(event)

    return result


def subject_tokens(text: str) -> set[str]:
    result = set()

    for token in normalize_text(text).split():

        if token in STOPWORDS:
            continue

        if token in GENERIC_SUBJECT_TOKENS:
            continue

        if is_year(token):
            continue

        if canonical_event(token):
            continue

        if len(token) < 3:
            continue

        result.add(token)

    return result


def is_distinctive(token: str) -> bool:
    if token in GENERIC_SUBJECT_TOKENS:
        return False

    if is_year(token):
        return False

    return len(token) >= 5


def canonical_similarity_text(text: str) -> str:
    result = []

    for token in normalize_text(text).split():

        event = canonical_event(token)

        if event:
            result.append(event)
        else:
            result.append(token)

    return " ".join(result)


def normalize_url(url: str) -> str:
    url = str(url or "").strip()

    if not url:
        return ""

    try:
        parts = urlsplit(url)

        return urlunsplit(
            (
                parts.scheme.lower(),
                parts.netloc.lower(),
                parts.path.rstrip("/"),
                "",
                "",
            )
        )

    except Exception:
        return url


def get_title(item: dict) -> str:
    return str(
        item.get("title")
        or item.get("titulo")
        or item.get("headline")
        or ""
    ).strip()


def get_url(item: dict) -> str:
    return str(
        item.get("url")
        or item.get("link")
        or item.get("enlace")
        or ""
    ).strip()


def parse_history_date(
    value: str,
) -> datetime | None:

    try:
        return datetime.fromisoformat(
            str(value or "")[:10]
        )

    except Exception:
        return None


def get_recent_history(
    history: list[dict],
) -> list[dict]:

    cutoff = (
        datetime.now()
        - timedelta(days=BLOCK_DAYS)
    )

    recent = []

    for item in history:

        date_value = parse_history_date(
            item.get("date")
            or item.get("fecha")
            or ""
        )

        if date_value is None:
            continue

        if date_value >= cutoff:
            recent.append(item)

    return recent


def has_material_new_development(
    current_title: str,
    old_title: str,
) -> tuple[bool, set[str]]:

    current_events = get_events(
        current_title
    )

    old_events = get_events(
        old_title
    )

    new_events = (
        current_events
        - old_events
    )

    material = (
        new_events
        & MATERIAL_NEW_EVENTS
    )

    return bool(material), material


def history_age_days(
    item: dict,
) -> int | None:

    value = (
        item.get("date")
        or item.get("fecha")
        or ""
    )

    parsed = parse_history_date(
        value
    )

    if parsed is None:
        return None

    return max(
        0,
        (datetime.now() - parsed).days,
    )


def compare_story(
    candidate: dict,
    old_item: dict,
) -> tuple[bool, str]:

    current_title = get_title(
        candidate
    )

    old_title = get_title(
        old_item
    )

    if not current_title or not old_title:
        return False, ""

    current_url = normalize_url(
        get_url(candidate)
    )

    old_url = normalize_url(
        get_url(old_item)
    )

    if (
        current_url
        and old_url
        and current_url == old_url
    ):
        return True, "misma URL"

    current_subject = subject_tokens(
        current_title
    )

    old_subject = subject_tokens(
        old_title
    )

    shared = (
        current_subject
        & old_subject
    )

    distinctive_shared = {
        token
        for token in shared
        if is_distinctive(token)
    }

    current_events = get_events(
        current_title
    )

    old_events = get_events(
        old_title
    )

    common_events = (
        current_events
        & old_events
    )

    current_similarity = (
        canonical_similarity_text(
            current_title
        )
    )

    old_similarity = (
        canonical_similarity_text(
            old_title
        )
    )

    similarity = float(
        fuzz.token_set_ratio(
            current_similarity,
            old_similarity,
        )
    )

    min_size = min(
        len(current_subject),
        len(old_subject),
    )

    containment = (
        len(shared) / min_size
        if min_size
        else 0.0
    )

    same_story = False

    age_days = history_age_days(
        old_item
    )

    strong_entity_count = len(
        distinctive_shared
    )

    # =====================================================
    # V4:
    # misma entidad NO significa misma noticia.
    #
    # 0-3 dias:
    # somos mas estrictos con republicaciones.
    #
    # 4-10 dias:
    # exigimos evidencia mucho mas fuerte.
    #
    # Sin fecha:
    # se trata como comparacion del mismo lote.
    # =====================================================

    if (
        age_days is None
        or age_days <= 3
    ):

        # Una entidad concreta +
        # mismo evento +
        # titulo muy parecido.
        if (
            strong_entity_count >= 1
            and common_events
            and similarity >= 84
        ):
            same_story = True

        # Dos entidades concretas +
        # mismo acontecimiento.
        elif (
            strong_entity_count >= 2
            and common_events
        ):
            same_story = True

        # Tres entidades concretas
        # con alta cobertura.
        elif (
            strong_entity_count >= 3
            and containment >= 0.60
        ):
            same_story = True


    elif age_days <= 10:

        # Pasados varios dias, una sola entidad
        # solo bloquea cuando el titular es casi
        # una repeticion del mismo acontecimiento.
        if (
            strong_entity_count >= 1
            and common_events
            and similarity >= 92
        ):
            same_story = True

        # Dos entidades + mismo evento +
        # cobertura importante.
        elif (
            strong_entity_count >= 2
            and common_events
            and containment >= 0.55
            and similarity >= 78
        ):
            same_story = True


    if not same_story:
        return False, ""

    is_new, new_events = (
        has_material_new_development(
            current_title,
            old_title,
        )
    )

    if is_new:
        return (
            False,
            "nuevo desarrollo fuerte: "
            + ", ".join(
                sorted(new_events)
            ),
        )

    shared_text = ", ".join(
        sorted(shared)[:8]
    )

    reason = (
        f"misma historia | "
        f"sim={similarity:.0f} | "
        f"shared={len(shared)}"
    )

    if shared_text:
        reason += (
            f" | anchors={shared_text}"
        )

    return True, reason


def load_json(
    path: Path,
    default,
):
    if not path.exists():
        return default

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return default


def main() -> None:

    print()
    print("=" * 64)
    print(
        " FILTRO ANTI-REPETICION V3 "
        f"({BLOCK_DAYS} DIAS)"
    )
    print("=" * 64)

    candidates = load_json(
        CANDIDATES_FILE,
        [],
    )

    history = load_json(
        HISTORY_FILE,
        [],
    )

    if not isinstance(
        candidates,
        list,
    ):
        raise RuntimeError(
            "candidates.json no contiene una lista."
        )

    if not isinstance(
        history,
        list,
    ):
        history = []

    recent_history = (
        get_recent_history(
            history
        )
    )

    print(
        f"Candidatas recibidas: "
        f"{len(candidates)}"
    )

    print(
        f"Noticias recientes en historial: "
        f"{len(recent_history)}"
    )

    kept = []
    blocked = []
    developments = []

    for candidate in candidates:

        blocked_reason = None
        matched_history = None
        development_reason = None

        for old_item in recent_history:

            is_duplicate, reason = (
                compare_story(
                    candidate,
                    old_item,
                )
            )

            if is_duplicate:
                blocked_reason = reason
                matched_history = old_item
                break

            if reason.startswith(
                "nuevo desarrollo fuerte:"
            ):
                development_reason = reason

        if blocked_reason:

            blocked.append(
                {
                    "candidate": candidate,
                    "reason": blocked_reason,
                    "history_match": matched_history,
                }
            )

        else:

            kept.append(candidate)

            if development_reason:

                developments.append(
                    {
                        "candidate": candidate,
                        "reason": development_reason,
                    }
                )

    CANDIDATES_FILE.write_text(
        json.dumps(
            kept,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    BLOCKED_FILE.write_text(
        json.dumps(
            blocked,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        f"Bloqueadas: {len(blocked)}"
    )
    print(
        f"Conservadas: {len(kept)}"
    )
    print(
        f"Nuevos desarrollos fuertes permitidos: "
        f"{len(developments)}"
    )

    if blocked:

        print()
        print("Ejemplos bloqueados:")

        for index, item in enumerate(
            blocked[:15],
            start=1,
        ):

            print()
            print(
                f"{index:02d}. "
                f"{get_title(item['candidate'])}"
            )
            print(
                "    Ya publicada: "
                f"{get_title(item['history_match'])}"
            )
            print(
                f"    Motivo: "
                f"{item['reason']}"
            )

    if developments:

        print()
        print(
            "Nuevos desarrollos permitidos:"
        )

        for index, item in enumerate(
            developments[:10],
            start=1,
        ):

            print(
                f"{index:02d}. "
                f"{get_title(item['candidate'])}"
            )
            print(
                f"    {item['reason']}"
            )

    print()
    print(
        "OK - filtro anti-repeticion "
        "V3 terminado."
    )


if __name__ == "__main__":
    main()