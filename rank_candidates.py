import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from rapidfuzz.fuzz import token_set_ratio


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "data" / "candidates.json"
OUTPUT_FILE = BASE_DIR / "data" / "shortlist.json"
BRANCH_OUTPUT_FILE = BASE_DIR / "data" / "shortlist_by_branch.json"

LIMA = ZoneInfo("America/Lima")

TOP_PER_BRANCH = 8
MAX_PER_SOURCE_PER_BRANCH = 3

FUZZY_DUPLICATE_THRESHOLD = 84
TOPIC_DUPLICATE_THRESHOLD = 72


# =========================================================
# NORMALIZACIÓN / TÉRMINOS
# =========================================================

def normalize(text):
    text = (text or "").lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def term_present(text, term):
    text = normalize(text)
    term = normalize(term)

    if not term:
        return False

    pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
    return re.search(pattern, text) is not None


def contains_any(text, terms):
    return any(term_present(text, term) for term in terms)


def count_terms(text, terms):
    return sum(1 for term in terms if term_present(text, term))


def matches_any(text, patterns):
    text = normalize(text)
    return any(re.search(pattern, text) for pattern in patterns)


def score_age(published):
    try:
        date = datetime.fromisoformat(published)
    except Exception:
        return 0

    now = datetime.now(LIMA)
    age_hours = (now - date).total_seconds() / 3600

    if age_hours <= 12:
        return 16
    if age_hours <= 24:
        return 12
    if age_hours <= 48:
        return 7
    if age_hours <= 72:
        return 3

    return -20


# =========================================================
# TOKENS / DEDUPLICACIÓN
# =========================================================

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being",
    "but", "by", "for", "from", "has", "have", "in", "into", "is",
    "it", "its", "of", "on", "or", "that", "the", "their", "this",
    "to", "was", "were", "will", "with", "you", "your",
    "new", "news", "official", "report", "reports", "says", "said",
    "2026", "2027", "2028",
}

EVENT_NOISE = STOPWORDS | {
    "release", "releases", "released", "date", "dates",
    "launch", "launches", "launched",
    "announcement", "announced",
    "trailer", "video", "update", "updated", "patch",
    "delay", "delayed",
    "season", "series", "movie", "film",
    "game", "games",
    "technology", "tech",
    "first", "look",
}

EVENT_FAMILIES = {
    "release": [
        "release date", "launch", "launches", "launched",
        "coming to", "arrives", "arriving",
    ],
    "delay": [
        "delay", "delayed", "postponed", "pushed back",
    ],
    "layoffs": [
        "layoff", "layoffs", "furlough", "furloughed",
        "job cuts", "transformation initiative",
    ],
    "subscription": [
        "game pass", "playstation plus", "ps plus",
    ],
    "showcase": [
        "showcase", "state of play", "nintendo direct",
        "xbox showcase",
    ],
    "renewal": [
        "renewed", "renewal", "greenlights", "greenlit",
    ],
    "cancellation": [
        "canceled", "cancelled", "cancellation",
    ],
    "lawsuit": [
        "lawsuit", "class action", "court",
    ],
    "update": [
        "update", "patch", "version",
    ],
}


def meaningful_tokens(text):
    return {
        word
        for word in normalize(text).split()
        if len(word) >= 3 and word not in STOPWORDS
    }


def entity_tokens(text):
    return {
        word
        for word in normalize(text).split()
        if len(word) >= 3 and word not in EVENT_NOISE
    }


def event_families(text):
    text = normalize(text)
    result = set()

    for family, terms in EVENT_FAMILIES.items():
        if contains_any(text, terms):
            result.add(family)

    return result


def are_duplicates(title_a, title_b):
    a = normalize(title_a)
    b = normalize(title_b)

    similarity = token_set_ratio(a, b)

    if similarity >= FUZZY_DUPLICATE_THRESHOLD:
        return True

    tokens_a = meaningful_tokens(a)
    tokens_b = meaningful_tokens(b)

    if not tokens_a or not tokens_b:
        return False

    common = tokens_a & tokens_b
    containment = len(common) / min(len(tokens_a), len(tokens_b))

    if (
        len(common) >= 4
        and (
            containment >= 0.55
            or similarity >= TOPIC_DUPLICATE_THRESHOLD
        )
    ):
        return True

    # V3.2:
    # Detectar el mismo sujeto con eventos equivalentes aunque un titular
    # diga "launches" y otro "release date", o uno "delay video" y otro
    # "launch delayed".
    families_a = event_families(a)
    families_b = event_families(b)

    shared_families = families_a & families_b

    entities_a = entity_tokens(a)
    entities_b = entity_tokens(b)

    common_entities = entities_a & entities_b

    if shared_families and len(common_entities) >= 2:
        return True

    # Si el nombre distintivo comparte 3+ tokens y ambos hablan de un evento
    # editorial, también se considera duplicado.
    if (
        len(common_entities) >= 3
        and families_a
        and families_b
    ):
        return True

    return False


# =========================================================
# FUENTES
# =========================================================

GAMING_PREMIUM = [
    "reuters", "associated press", "bloomberg",
    "gamesindustry.biz", "video games chronicle", "vgc",
    "the verge", "ign", "gamespot", "eurogamer",
    "pc gamer", "polygon",
]

GAMING_GOOD = [
    "windows central", "rock paper shotgun", "nintendo life",
    "push square", "playstation lifestyle", "game informer",
    "destructoid", "kotaku", "gematsu", "vg247",
    "gamesradar", "tom's hardware", "digital foundry",
    "dexerto", "esports insider",
]

TECH_PREMIUM = [
    "reuters", "associated press", "bloomberg",
    "the verge", "techcrunch", "arstechnica", "ars technica",
    "wired", "engadget", "cnet", "tom's hardware",
    "the register", "bleepingcomputer",
]

TECH_GOOD = [
    "9to5google", "9to5mac", "macrumors",
    "android authority", "android police", "windows central",
    "zdnet", "pcmag", "techradar", "gsmarena",
    "venturebeat", "the next web", "forbes",
    "wall street journal", "wsj",
]

POP_PREMIUM = [
    "reuters", "associated press", "variety",
    "hollywood reporter", "deadline", "entertainment weekly",
    "empire", "anime news network", "ign",
]

POP_GOOD = [
    "collider", "comicbook", "screen rant",
    "gamesradar", "crunchyroll", "polygon",
    "the wrap", "indiewire", "tvline", "comingsoon",
]

LOW_PRIORITY = [
    "tech-insider.org", "augustman", "augustman singapore",
    "the movie blog", "vital thrills", "whistleout",
    "ua.news", "toy people", "imdb.com", "screenrant",
    "sportskeeda", "gamerant", "stocktwits",
    "ai reset to zero", "mshale", "mandatory.com",
]


def source_contains(source, terms):
    source = normalize(source)
    return any(normalize(term) in source for term in terms)


def score_source(source, branch):
    source = normalize(source)

    if branch == "gaming":
        premium = GAMING_PREMIUM
        good = GAMING_GOOD
    elif branch == "tecnologia":
        premium = TECH_PREMIUM
        good = TECH_GOOD
    else:
        premium = POP_PREMIUM
        good = POP_GOOD

    if source_contains(source, premium):
        return 30

    if source_contains(source, good):
        return 20

    if source_contains(source, LOW_PRIORITY):
        return -12

    return 5


# =========================================================
# PENALIZACIONES GENERALES
# =========================================================

DEAL_TERMS = [
    "deal", "discount", "coupon", "save",
    "best price", "price drop", "cheap", "sale",
]

GUIDE_TERMS = [
    "how to", "complete guide", "guide to",
    "everything you need to know", "what you need to know",
    "where to buy", "where to watch", "tips and tricks",
]

LISTICLE_PATTERNS = [
    r"\bthe\s+\d+\s+best\b",
    r"\b\d+\s+best\b",
    r"\btop\s+\d+\b",
    r"\bbest\s+.+\s+(?:games|movies|shows|phones|apps|chatbots)\b",
]

EVERGREEN_TERMS = [
    "complete guide", "release dates", "premiere dates",
    "coming soon", "upcoming games", "upcoming movies",
    "everything coming to", "everything leaving",
    "schedule announced", "schedule for",
]

STRONG_SPECULATION = [
    "rumor", "rumour", "leak", "leaked",
    "fans think", "fans believe", "what to expect",
    "looking likely", "might be", "could be", "may be",
    "report suggests",
]

SOFT_SPECULATION = [
    "reportedly", "probably", "likely", "appears to",
]


def apply_general_penalties(title, score, reasons):
    if contains_any(title, DEAL_TERMS):
        score -= 35
        reasons.append("oferta -35")

    if contains_any(title, GUIDE_TERMS):
        score -= 35
        reasons.append("guía/explainer -35")

    if matches_any(title, LISTICLE_PATTERNS):
        score -= 42
        reasons.append("listicle -42")

    if contains_any(title, EVERGREEN_TERMS):
        score -= 38
        reasons.append("evergreen -38")

    strong_count = count_terms(title, STRONG_SPECULATION)
    if strong_count:
        points = min(strong_count * 12, 30)
        score -= points
        reasons.append(f"especulación fuerte -{points}")

    soft_count = count_terms(title, SOFT_SPECULATION)
    if soft_count:
        points = min(soft_count * 5, 10)
        score -= points
        reasons.append(f"especulación suave -{points}")

    return score, reasons


# =========================================================
# GAMING
# =========================================================

GAMING_IMPACT = [
    "acquisition", "acquired", "merger",
    "layoff", "layoffs", "furlough", "shutdown", "closure",
    "cancelled", "canceled", "delay", "delayed",
    "lawsuit", "price increase", "price hike",
    "game pass", "playstation plus", "ps plus",
    "exclusive", "exclusivity",
]

GAMING_ANNOUNCEMENT = [
    "announced", "announces", "reveals", "revealed",
    "release date", "launches", "showcase",
    "state of play", "nintendo direct", "xbox showcase",
    "update", "expansion",
]

GAMING_BRANDS = [
    "playstation", "sony", "xbox", "microsoft",
    "nintendo", "steam", "valve", "epic games",
    "electronic arts", "ea", "ubisoft", "activision",
    "blizzard", "rockstar", "capcom", "konami",
    "square enix", "bandai namco", "sega",
    "riot games", "valorant", "league of legends",
]

ESPORTS_TERMS = [
    "esports", "valorant", "league of legends",
    "vct", "lck", "lec", "lcs",
]

GAMING_MINOR_MEDIA = [
    "official trailer", "launch trailer", "gameplay trailer",
    "announcement trailer", "teaser trailer",
    "announcement video", "official video",
]

GAMING_LOW_VALUE = [
    "interview", "creator says", "developer says",
    "producer says", "our impressions",
    "hands on", "hands-on",
]


def score_gaming(item):
    title = normalize(item.get("title", ""))
    source = item.get("source", "")

    score = 0
    reasons = []

    p = score_source(source, "gaming")
    score += p
    reasons.append(f"fuente {p:+d}")

    p = score_age(item.get("published", ""))
    score += p
    reasons.append(f"actualidad {p:+d}")

    impact = count_terms(title, GAMING_IMPACT)
    if impact:
        p = min(impact * 8, 24)
        score += p
        reasons.append(f"impacto {p:+d}")

    announcements = count_terms(title, GAMING_ANNOUNCEMENT)
    if announcements:
        p = min(announcements * 6, 18)
        score += p
        reasons.append(f"anuncio {p:+d}")

    brands = count_terms(title, GAMING_BRANDS)
    if brands:
        p = min(brands * 5, 15)
        score += p
        reasons.append(f"marca {p:+d}")

    if contains_any(title, ESPORTS_TERMS):
        score += 8
        reasons.append("esports +8")

    if contains_any(title, GAMING_MINOR_MEDIA):
        if (
            term_present(title, "release date")
            or term_present(title, "delayed")
            or term_present(title, "delay")
            or term_present(title, "coming to")
        ):
            score -= 12
            reasons.append("video/tráiler -12")
        else:
            score -= 22
            reasons.append("video/tráiler menor -22")

    if contains_any(title, GAMING_LOW_VALUE):
        score -= 18
        reasons.append("entrevista/opinión -18")

    score, reasons = apply_general_penalties(
        title,
        score,
        reasons,
    )

    return score, reasons


# =========================================================
# TECNOLOGÍA / IA
# =========================================================

TECH_IMPACT = [
    "artificial intelligence", "ai", "openai", "gemini", "anthropic",
    "iphone", "ios", "android", "windows",
    "nvidia", "amd", "intel", "snapdragon",
    "gpu", "cpu", "chip", "semiconductor",
    "data breach", "cybersecurity", "hack", "hacked",
    "vulnerability", "outage", "ban", "regulation",
    "antitrust", "lawsuit", "acquisition", "acquires", "merger",
]

TECH_LAUNCH = [
    "launches", "launched", "announces", "announced",
    "unveils", "reveals", "released", "rolls out",
    "new model", "new feature", "update",
]

TECH_MAJOR_BRANDS = [
    "openai", "google", "microsoft", "apple", "samsung",
    "nvidia", "amd", "intel", "meta", "tiktok",
    "instagram", "amazon", "anthropic", "qualcomm",
]

TECH_NICHE_B2B = [
    "finance teams", "spend management", "procurement",
    "control plane for enterprises", "enterprise workflow",
    "channel partners", "business decisions", "business future",
]

TECH_THOUGHT_LEADERSHIP = [
    "why businesses should", "how businesses can",
    "the future of business", "what businesses need to know",
    "decisions that could shape",
]

TECH_FINANCE_NOISE = [
    "premarket", "shares rise", "shares fall",
    "stock rises", "stock falls", "stock price",
    "investors", "wall street", "earnings preview",
]

TECH_PODCAST_NOISE = [
    "podcast", "episode", "ard",
]

TECH_ANALYSIS_NOISE = [
    "how ai could", "why ai could",
    "what ai means", "best ai chatbots",
    "why now is a good time",
]

TECH_STARTUP_FUNDING = [
    "raises", "raised", "funding round", "seed round",
    "series a", "series b", "series c", "incubated",
]


def score_technology(item):
    title = normalize(item.get("title", ""))
    source = item.get("source", "")

    score = 0
    reasons = []

    p = score_source(source, "tecnologia")
    score += p
    reasons.append(f"fuente {p:+d}")

    p = score_age(item.get("published", ""))
    score += p
    reasons.append(f"actualidad {p:+d}")

    impact = count_terms(title, TECH_IMPACT)
    if impact:
        p = min(impact * 7, 28)
        score += p
        reasons.append(f"impacto tech {p:+d}")

    launches = count_terms(title, TECH_LAUNCH)
    if launches:
        p = min(launches * 5, 15)
        score += p
        reasons.append(f"lanzamiento {p:+d}")

    brands = count_terms(title, TECH_MAJOR_BRANDS)
    if brands:
        p = min(brands * 5, 15)
        score += p
        reasons.append(f"marca tech {p:+d}")

    if contains_any(
        title,
        [
            "data breach", "zero day", "zero-day",
            "critical vulnerability", "major outage",
            "security flaw", "cyberattack",
        ]
    ):
        score += 12
        reasons.append("seguridad +12")

    if contains_any(title, TECH_NICHE_B2B):
        score -= 20
        reasons.append("B2B nicho -20")

    if contains_any(title, TECH_THOUGHT_LEADERSHIP):
        score -= 28
        reasons.append("opinión empresarial -28")

    if contains_any(title, TECH_FINANCE_NOISE):
        score -= 28
        reasons.append("ruido financiero -28")

    if contains_any(title, TECH_PODCAST_NOISE):
        score -= 30
        reasons.append("podcast -30")

    if contains_any(title, TECH_ANALYSIS_NOISE):
        score -= 26
        reasons.append("análisis/evergreen -26")

    if contains_any(title, TECH_STARTUP_FUNDING):
        # No se elimina; solo baja frente a noticias de consumo,
        # plataformas, IA importante, seguridad o hardware.
        score -= 18
        reasons.append("startup/funding -18")

    score, reasons = apply_general_penalties(
        title,
        score,
        reasons,
    )

    return score, reasons


# =========================================================
# CULTURA POP
# =========================================================

POP_IMPACT = [
    "renewed", "renewal", "canceled", "cancelled", "cancellation",
    "release date", "premiere date", "casting", "cast",
    "trailer", "teaser", "box office", "season",
    "movie", "film", "series", "anime", "manga",
    "adaptation", "live action", "live-action",
]

POP_BRANDS = [
    "marvel", "dc", "star wars", "disney", "pixar",
    "netflix", "hbo", "max", "prime video", "amazon",
    "crunchyroll", "warner bros", "universal",
    "paramount", "sony pictures",
]

POP_ANNOUNCEMENT = [
    "announced", "announces", "reveals", "revealed",
    "confirmed", "confirms", "renewed",
    "canceled", "cancelled", "trailer", "teaser",
    "release date", "premiere date", "casting",
]

POP_LOW_VALUE = [
    "streaming pleasure", "how i m saving",
    "how i am saving", "streaming services in 2026",
    "complete guide", "schedule announced", "schedule for",
]

POP_SEO_NOISE = [
    "ott platforms", "ott platform",
    "review trailer star cast",
    "star cast songs posters",
    "songs posters",
    "release date cast plot",
]

POP_MINOR_TRAILER = [
    "character trailer", "character trailers",
    "theme song", "theme songs",
    "opening theme", "ending theme",
]

POP_LEAK_NOISE = [
    "plot leaks", "leaks", "leaked",
    "first look leaks",
]

POP_ROUNDUP_NOISE = [
    "all tv shows canceled",
    "all tv shows cancelled",
    "all shows canceled",
    "all shows cancelled",
    "everything canceled",
    "everything cancelled",
]


def score_pop(item):
    title = normalize(item.get("title", ""))
    source = item.get("source", "")

    score = 0
    reasons = []

    p = score_source(source, "cultura_pop")
    score += p
    reasons.append(f"fuente {p:+d}")

    p = score_age(item.get("published", ""))
    score += p
    reasons.append(f"actualidad {p:+d}")

    impact = count_terms(title, POP_IMPACT)
    if impact:
        p = min(impact * 6, 24)
        score += p
        reasons.append(f"impacto pop {p:+d}")

    brands = count_terms(title, POP_BRANDS)
    if brands:
        p = min(brands * 5, 15)
        score += p
        reasons.append(f"marca pop {p:+d}")

    announcements = count_terms(title, POP_ANNOUNCEMENT)
    if announcements:
        p = min(announcements * 5, 15)
        score += p
        reasons.append(f"anuncio pop {p:+d}")

    if contains_any(
        title,
        [
            "box office record", "record opening", "record debut",
            "renewed for season", "canceled after", "cancelled after",
        ]
    ):
        score += 8
        reasons.append("impacto entretenimiento +8")

    if contains_any(title, POP_LOW_VALUE):
        score -= 32
        reasons.append("contenido bajo valor -32")

    if contains_any(title, POP_SEO_NOISE):
        score -= 40
        reasons.append("SEO agregador -40")

    if contains_any(title, POP_MINOR_TRAILER):
        score -= 18
        reasons.append("tráiler menor -18")

    if contains_any(title, POP_LEAK_NOISE):
        score -= 28
        reasons.append("leak/rumor pop -28")

    if contains_any(title, POP_ROUNDUP_NOISE):
        score -= 35
        reasons.append("roundup pop -35")

    score, reasons = apply_general_penalties(
        title,
        score,
        reasons,
    )

    return score, reasons


# =========================================================
# ASIGNACIÓN DE RAMA
# =========================================================

SCORERS = {
    "gaming": score_gaming,
    "tecnologia": score_technology,
    "cultura_pop": score_pop,
}


def allowed_branches(item):
    branches = item.get("categories_seen") or []

    if not branches:
        branch = item.get("category_internal")
        if branch:
            branches = [branch]

    return [
        branch
        for branch in branches
        if branch in SCORERS
    ]


def choose_primary_branch(item):
    branches = allowed_branches(item)

    if not branches:
        return None, -999, []

    results = []

    for branch in branches:
        score, reasons = SCORERS[branch](item)
        results.append((score, branch, reasons))

    results.sort(
        key=lambda row: row[0],
        reverse=True,
    )

    best_score, best_branch, best_reasons = results[0]

    return best_branch, best_score, best_reasons


# =========================================================
# DEDUPLICACIÓN POR RAMA
# =========================================================

def deduplicate_ranked(items):
    accepted = []
    removed = 0

    for candidate in items:
        duplicate = False

        for existing in accepted:
            if are_duplicates(
                candidate.get("title", ""),
                existing.get("title", ""),
            ):
                duplicate = True
                removed += 1
                break

        if not duplicate:
            accepted.append(candidate)

    return accepted, removed


# =========================================================
# MAIN
# =========================================================

def main():
    items = json.loads(
        INPUT_FILE.read_text(encoding="utf-8")
    )

    print()
    print("=" * 60)
    print(
        " GAMING NEWS GENERATOR - "
        "RANKING MULTITEMÁTICO V3.2"
    )
    print("=" * 60)
    print()
    print(f"Candidatas recibidas: {len(items)}")
    print()

    branch_pools = {
        "gaming": [],
        "tecnologia": [],
        "cultura_pop": [],
    }

    for item in items:
        branch, score, reasons = choose_primary_branch(item)

        if branch is None:
            continue

        copy = dict(item)
        copy["editorial_branch"] = branch
        copy["editorial_score"] = score
        copy["score_reasons"] = reasons

        branch_pools[branch].append(copy)

    final_by_branch = {}
    combined = []

    for branch in (
        "gaming",
        "tecnologia",
        "cultura_pop",
    ):
        pool = branch_pools[branch]

        pool.sort(
            key=lambda item: item["editorial_score"],
            reverse=True,
        )

        deduped, removed = deduplicate_ranked(pool)

        source_counts = defaultdict(int)
        top = []

        for item in deduped:
            source_key = normalize(
                item.get("source", "Sin fuente")
                or "Sin fuente"
            )

            if (
                source_counts[source_key]
                >= MAX_PER_SOURCE_PER_BRANCH
            ):
                continue

            source_counts[source_key] += 1

            copy = dict(item)
            copy["branch_rank"] = len(top) + 1
            top.append(copy)

            if len(top) >= TOP_PER_BRANCH:
                break

        final_by_branch[branch] = top
        combined.extend(top)

        print("-" * 60)
        print(f" {branch.upper()}")
        print("-" * 60)
        print()
        print(f"Asignadas a rama: {len(pool)}")
        print(f"Duplicados eliminados: {removed}")
        print(f"TOP para Terra: {len(top)}")
        print()

        for item in top:
            print(
                f'{item["branch_rank"]:02d}. '
                f'[{item["editorial_score"]:+d}] '
                f'{item["title"]}'
            )

            print(f'    Fuente: {item["source"]}')

            print(
                "    "
                + " | ".join(
                    item["score_reasons"]
                )
            )

            print()

    for index, item in enumerate(
        combined,
        start=1,
    ):
        item["shortlist_id"] = index

    OUTPUT_FILE.write_text(
        json.dumps(
            combined,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    BRANCH_OUTPUT_FILE.write_text(
        json.dumps(
            final_by_branch,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 60)
    print(" RESULTADO FINAL")
    print("=" * 60)
    print()
    print(f"Gaming:      {len(final_by_branch['gaming'])}")
    print(f"Tecnología:  {len(final_by_branch['tecnologia'])}")
    print(f"Cultura Pop: {len(final_by_branch['cultura_pop'])}")
    print()
    print(f"Total candidatas para Terra: {len(combined)}")
    print()
    print("Archivo combinado:")
    print(OUTPUT_FILE)
    print()
    print("Archivo por ramas:")
    print(BRANCH_OUTPUT_FILE)
    print()
    print("Costo OpenAI API: $0.00")
    print()


if __name__ == "__main__":
    main()
