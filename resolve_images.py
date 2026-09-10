import json
import re
import unicodedata
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from googlenewsdecoder import gnewsdecoder
from PIL import Image


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

NEWS_FILE = BASE_DIR / "data" / "noticias.json"
OUTPUT_FILE = BASE_DIR / "data" / "image_candidates.json"
CONFIG_FILE = BASE_DIR / "image_config.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "of", "to", "in", "on", "with",
    "from", "by", "is", "are", "has", "have", "will", "its", "this", "that",
    "new", "news", "release", "date", "announced", "announce", "reveals", "revealed",
    "reportedly", "expect", "update", "updates", "exclusive", "footage", "week", "same",
    "day", "currently", "behind", "majority", "staff", "studio", "game",
    "official", "first", "look", "launch", "launches", "launched",
    "season", "movie", "film", "series", "show", "shows", "trailer", "teaser",
    "technology", "tech", "company", "companies",
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "o",
    "para", "por", "en", "con", "desde", "es", "son", "su", "sus", "nuevo", "nueva",
    "noticia",
}

GENERIC_WORDS = {
    "gaming", "games", "xbox", "playstation", "sony", "nintendo", "steam", "pc",
    "ps5", "ps4", "switch", "series", "console", "consoles",
    "ai", "technology", "tech", "movie", "film", "show", "season", "streaming",
}

BAD_IMAGE_WORDS = {
    "logo", "favicon", "icon", "icons", "avatar", "placeholder", "sprite", "badge",
    "tracking", "pixel", "brandmark", "wordmark", "default", "fallback",
}

PREFERRED_WORDS = {
    "keyart", "key", "art", "cover", "poster", "artwork", "official", "hero", "featured",
    "screenshot", "gameplay", "still", "photo", "image",
}

BAD_EXTENSIONS = (".svg", ".gif", ".ico")

BAD_PATHS = (
    "/favicon", "/icons/", "/icon/", "/avatars/", "/sprite/", "/sprites/", "/badges/",
    "/_next/static/media/",
)


# =========================================================
# CALIDAD DE FUENTES V4.2
# =========================================================

PREMIUM_SOURCE_TERMS = {
    "reuters",
    "associated press",
    "ap news",
    "the verge",
    "techcrunch",
    "tom s hardware",
    "ars technica",
    "wired",
    "engadget",
    "cnet",
    "zdnet",
    "ign",
    "gamespot",
    "eurogamer",
    "pc gamer",
    "polygon",
    "video games chronicle",
    "vgc",
    "hollywood reporter",
    "variety",
    "deadline",
    "entertainment weekly",
    "anime news network",
    "crunchyroll",
    "comingsoon",
}

GOOD_SOURCE_TERMS = {
    "windows central",
    "android authority",
    "macrumors",
    "9to5google",
    "9to5mac",
    "gamesradar",
    "nintendo life",
    "push square",
    "playstation lifestyle",
    "vgchartz",
    "venturebeat",
    "the register",
    "bleepingcomputer",
    "collider",
    "indiewire",
    "tvline",
}

OFFICIAL_DOMAIN_TERMS = {
    "nvidia.com",
    "mediatek.com",
    "amd.com",
    "intel.com",
    "microsoft.com",
    "apple.com",
    "google.com",
    "blog.google",
    "openai.com",
    "anthropic.com",
    "playstation.com",
    "xbox.com",
    "nintendo.com",
    "ea.com",
    "ubisoft.com",
    "capcom.com",
    "konami.com",
    "netflix.com",
    "disney.com",
    "marvel.com",
    "dc.com",
    "warnerbros.com",
    "paramount.com",
    "primevideo.com",
    "crunchyroll.com",
}

LOW_TRUST_SOURCE_TERMS = {
    "watcher guru",
    "citybiz",
    "mandatory",
    "mshale",
    "whistleout",
    "tech insider",
    "ua news",
    "augustman",
    "movie blog",
    "vital thrills",
    "twaslnews",
    "شبكة تواصل",
}


# =========================================================
# UTILIDADES
# =========================================================

def normalize(text):
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().strip()


def tokens(text):
    return set(
        re.findall(
            r"[a-z0-9]+",
            normalize(text),
        )
    )


def domain(url):
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def clean_title(title, source=""):
    title = str(title or "").strip()
    source = str(source or "").strip()

    if source:
        low_title = title.lower()
        low_source = source.lower()

        for sep in (
            " - ",
            " — ",
            " – ",
        ):
            suffix = sep + low_source

            if low_title.endswith(
                suffix
            ):
                return title[
                    :-len(suffix)
                ].strip()

    return title


def source_quality_bonus(
    source_name,
    article_url,
):
    source_norm = normalize(
        source_name
    )

    host = domain(
        article_url
    )

    if any(
        official in host
        for official in OFFICIAL_DOMAIN_TERMS
    ):
        return 45

    if any(
        term in source_norm
        for term in PREMIUM_SOURCE_TERMS
    ):
        return 30

    if any(
        term in source_norm
        for term in GOOD_SOURCE_TERMS
    ):
        return 15

    if any(
        term in source_norm
        for term in LOW_TRUST_SOURCE_TERMS
    ):
        return -30

    return 0


def url_topic_tokens(
    article_url
):
    path = normalize(
        urlparse(
            article_url
        ).path.replace(
            "-",
            " ",
        ).replace(
            "_",
            " ",
        )
    )

    return {
        word
        for word in tokens(
            path
        )
        if (
            len(word) >= 3
            and word not in STOPWORDS
        )
    }


def topic_keywords(
    title,
    source="",
    article_url="",
):
    base = {
        word
        for word in tokens(
            clean_title(
                title,
                source,
            )
        )
        if (
            len(word) >= 3
            and word not in STOPWORDS
        )
    }

    return (
        base
        | url_topic_tokens(
            article_url
        )
    )


def distinctive_title_tokens(
    title,
    source="",
):
    clean = clean_title(
        title,
        source,
    )

    result = []

    for word in re.findall(
        r"[a-z0-9]+",
        normalize(
            clean
        ),
    ):
        if (
            len(word) < 3
            or word in STOPWORDS
            or word in GENERIC_WORDS
        ):
            continue

        if word not in result:
            result.append(
                word
            )

    return result


def is_google_news(url):
    return (
        domain(url)
        == "news.google.com"
        or "/rss/articles/"
        in str(url)
        or "/read/"
        in str(url)
    )


def resolve_google_news(url):
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

    return ""


def usable_url(url):
    if not url:
        return False

    lower = (
        str(url)
        .split("?")[0]
        .split("#")[0]
        .lower()
    )

    if (
        lower.startswith(
            "data:"
        )
        or lower.endswith(
            BAD_EXTENSIONS
        )
    ):
        return False

    if any(
        path in lower
        for path in BAD_PATHS
    ):
        return False

    return True


def best_srcset(srcset):
    options = []

    for part in str(
        srcset or ""
    ).split(","):
        pieces = (
            part.strip()
            .split()
        )

        if not pieces:
            continue

        weight = 0

        if len(
            pieces
        ) > 1:
            descriptor = (
                pieces[1]
                .lower()
            )

            try:
                if descriptor.endswith(
                    "w"
                ):
                    weight = int(
                        descriptor[:-1]
                    )

                elif descriptor.endswith(
                    "x"
                ):
                    weight = int(
                        float(
                            descriptor[:-1]
                        )
                        * 1000
                    )

            except Exception:
                pass

        options.append(
            (
                weight,
                pieces[0],
            )
        )

    return max(
        options,
        default=(
            0,
            "",
        ),
    )[1]


# =========================================================
# RECOLECCIÓN DE IMÁGENES
# =========================================================

def add_candidate(
    items,
    page_url,
    image_url,
    kind,
    text="",
):
    if not image_url:
        return

    if image_url.startswith(
        "//"
    ):
        image_url = (
            "https:"
            + image_url
        )

    image_url = urljoin(
        page_url,
        image_url,
    )

    if not usable_url(
        image_url
    ):
        return

    items.append({
        "url": image_url,
        "kind": kind,
        "text": str(
            text or ""
        ),
    })


def collect_jsonld_images(
    value,
    output,
):
    if isinstance(
        value,
        str,
    ):
        if value.startswith(
            (
                "http://",
                "https://",
                "//",
            )
        ):
            output.append(
                value
            )

    elif isinstance(
        value,
        list,
    ):
        for item in value:
            collect_jsonld_images(
                item,
                output,
            )

    elif isinstance(
        value,
        dict,
    ):
        for key in (
            "url",
            "contentUrl",
            "thumbnailUrl",
        ):
            if key in value:
                collect_jsonld_images(
                    value[key],
                    output,
                )


def collect_candidates(
    html,
    page_url,
):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    items = []

    # V4.2: el título de la página sirve como contexto semántico
    # para OG/Twitter cuando el medio usa filenames genéricos.
    page_title = ""

    og_title = soup.find(
        "meta",
        attrs={
            "property": "og:title"
        },
    )

    if (
        og_title
        and og_title.get(
            "content"
        )
    ):
        page_title = str(
            og_title.get(
                "content"
            )
        )

    if not page_title:
        title_tag = soup.find(
            "title"
        )

        if title_tag:
            page_title = (
                title_tag.get_text(
                    " ",
                    strip=True,
                )
            )

    og_alt_tag = soup.find(
        "meta",
        attrs={
            "property": "og:image:alt"
        },
    )

    og_alt = (
        og_alt_tag.get(
            "content",
            "",
        )
        if og_alt_tag
        else ""
    )

    # V4.3:
    # Solo evidencia propia de la imagen.
    # El t?tulo de la p?gina NO cuenta como relevancia visual.
    og_context = str(
        og_alt or ""
    ).strip()

    for prop in (
        "og:image",
        "og:image:url",
        "og:image:secure_url",
    ):
        for tag in soup.find_all(
            "meta",
            attrs={
                "property": prop
            },
        ):
            add_candidate(
                items,
                page_url,
                tag.get(
                    "content",
                    "",
                ),
                "og",
                og_context,
            )

    twitter_alt_tag = soup.find(
        "meta",
        attrs={
            "name": "twitter:image:alt"
        },
    )

    twitter_alt = (
        twitter_alt_tag.get(
            "content",
            "",
        )
        if twitter_alt_tag
        else ""
    )

    # V4.3:
    # Solo evidencia propia de la imagen.
    twitter_context = str(
        twitter_alt or ""
    ).strip()

    for name in (
        "twitter:image",
        "twitter:image:src",
    ):
        for tag in soup.find_all(
            "meta",
            attrs={
                "name": name
            },
        ):
            add_candidate(
                items,
                page_url,
                tag.get(
                    "content",
                    "",
                ),
                "twitter",
                twitter_context,
            )

    for script in soup.find_all(
        "script",
        attrs={
            "type": "application/ld+json"
        },
    ):
        try:
            raw = (
                script.string
                or script.get_text(
                    "",
                    strip=False,
                )
            )

            data = json.loads(
                raw
            )

        except Exception:
            continue

        def inspect(obj):
            if isinstance(
                obj,
                dict,
            ):
                if "image" in obj:
                    urls = []

                    collect_jsonld_images(
                        obj[
                            "image"
                        ],
                        urls,
                    )

                    for image_url in urls:
                        # V4.3:
                        # JSON-LD no hereda el t?tulo del art?culo.
                        # Si la URL de la imagen es espec?fica,
                        # el scoring podr? detectarlo por separado.
                        add_candidate(
                            items,
                            page_url,
                            image_url,
                            "jsonld",
                            "",
                        )

                for value in obj.values():
                    inspect(
                        value
                    )

            elif isinstance(
                obj,
                list,
            ):
                for value in obj:
                    inspect(
                        value
                    )

        inspect(
            data
        )

    article = (
        soup.find(
            "article"
        )
        or soup.find(
            "main"
        )
        or soup
    )

    for img in article.find_all(
        "img",
        limit=140,
    ):
        src = (
            best_srcset(
                img.get(
                    "srcset"
                )
                or img.get(
                    "data-srcset"
                )
                or ""
            )
            or img.get(
                "data-src"
            )
            or img.get(
                "data-lazy-src"
            )
            or img.get(
                "data-original"
            )
            or img.get(
                "src"
            )
            or ""
        )

        caption = ""

        figure = img.find_parent(
            "figure"
        )

        if figure:
            figcaption = figure.find(
                "figcaption"
            )

            if figcaption:
                caption = (
                    figcaption.get_text(
                        " ",
                        strip=True,
                    )
                )

        text = " ".join(
            [
                img.get(
                    "alt",
                    "",
                ),
                img.get(
                    "title",
                    "",
                ),
                caption,
            ]
        )

        add_candidate(
            items,
            page_url,
            src,
            "article",
            text,
        )

    unique = {}

    for item in items:
        image_url = item[
            "url"
        ]

        if image_url not in unique:
            unique[
                image_url
            ] = item

        elif len(
            item[
                "text"
            ]
        ) > len(
            unique[
                image_url
            ][
                "text"
            ]
        ):
            unique[
                image_url
            ][
                "text"
            ] = item[
                "text"
            ]

    return list(
        unique.values()
    )


# =========================================================
# SCORING
# =========================================================

def filename_tokens(url):
    path = normalize(
        urlparse(
            url
        ).path
    )

    return tokens(
        path.replace(
            "-",
            " ",
        ).replace(
            "_",
            " ",
        ).replace(
            ".",
            " ",
        )
    )


def candidate_score(
    candidate,
    keywords,
):
    url_tokens = filename_tokens(
        candidate[
            "url"
        ]
    )

    text_tokens = tokens(
        candidate.get(
            "text",
            "",
        )
    )

    specific_topic = (
        keywords
        - GENERIC_WORDS
    )

    matched_url_specific = (
        specific_topic
        & url_tokens
    )

    matched_text_specific = (
        specific_topic
        & text_tokens
    )

    matched_url_generic = (
        GENERIC_WORDS
        & url_tokens
    )

    bad_url = (
        BAD_IMAGE_WORDS
        & url_tokens
    )

    bad_text = (
        BAD_IMAGE_WORDS
        & text_tokens
    )

    score = {
        "article": 45,
        "jsonld": 32,
        "og": 28,
        "twitter": 22,
    }.get(
        candidate[
            "kind"
        ],
        0,
    )

    # URL/filename sigue siendo señal fuerte.
    score += min(
        len(
            matched_url_specific
        ),
        5,
    ) * 38

    # V4.2: el contexto textual pesa un poco más.
    # Esto ayuda a tecnología/cultura pop cuando el CDN usa filenames
    # poco descriptivos.
    score += min(
        len(
            matched_text_specific
        ),
        5,
    ) * 14

    if (
        candidate[
            "kind"
        ]
        == "article"
        and matched_url_specific
    ):
        score += 20

    if (
        PREFERRED_WORDS
        & url_tokens
    ):
        score += 20

    elif (
        PREFERRED_WORDS
        & text_tokens
    ):
        score += 8

    if bad_url:
        score -= 240

    elif (
        bad_text
        and not matched_url_specific
    ):
        score -= 110

    if (
        matched_url_generic
        and not matched_url_specific
        and len(
            matched_text_specific
        ) < 2
    ):
        score -= 140

    meaningful_url = (
        url_tokens
        - GENERIC_WORDS
        - BAD_IMAGE_WORDS
        - {
            "jpg",
            "jpeg",
            "png",
            "webp",
            "image",
            "img",
        }
    )

    if (
        len(
            meaningful_url
        ) <= 1
        and not matched_url_specific
        and len(
            matched_text_specific
        ) < 2
    ):
        score -= 45

    candidate[
        "matched_url_specific"
    ] = sorted(
        matched_url_specific
    )

    candidate[
        "matched_text_specific"
    ] = sorted(
        matched_text_specific
    )

    candidate[
        "matched_url_generic"
    ] = sorted(
        matched_url_generic
    )

    candidate[
        "bad_url_terms"
    ] = sorted(
        bad_url
    )

    return score


# =========================================================
# HTTP / BROWSER
# =========================================================

def fetch_requests(
    url,
    timeout,
):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=timeout,
        allow_redirects=True,
    )

    response.raise_for_status()

    return (
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
                timeout=30000,
            )

            page.wait_for_timeout(
                1500
            )

            return (
                page.url,
                page.content(),
            )

        finally:
            browser.close()


def fetch_article(
    url,
    timeout,
    browser_fallback=True,
):
    try:
        return fetch_requests(
            url,
            timeout,
        )

    except Exception:
        if not browser_fallback:
            raise

        return fetch_browser(
            url
        )


def probe_image(
    url,
    timeout,
    referer="",
):
    try:
        headers = dict(
            HEADERS
        )

        if referer:
            headers[
                "Referer"
            ] = referer

        headers[
            "Accept"
        ] = (
            "image/avif,image/webp,"
            "image/apng,image/*,*/*;q=0.8"
        )

        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
        )

        response.raise_for_status()

        content_type = (
            response.headers.get(
                "content-type",
                "",
            )
            .split(";")[0]
            .strip()
            .lower()
        )

        if (
            "svg"
            in content_type
            or content_type
            in {
                "text/html",
                "application/xhtml+xml",
            }
        ):
            return None

        image = Image.open(
            BytesIO(
                response.content
            )
        )

        image.load()

        width, height = (
            image.size
        )

        if (
            width < 600
            or height < 338
        ):
            return None

        # Rechazar ratios absurdamente verticales/horizontales para tarjetas.
        ratio = (
            width
            / max(
                height,
                1,
            )
        )

        if (
            ratio < 0.75
            or ratio > 2.6
        ):
            return None

        return {
            "width": width,
            "height": height,
            "format": (
                image.format
                or ""
            ),
            "content_type": content_type,
        }

    except Exception:
        return None


def rank_and_validate(
    candidates,
    keywords,
    timeout,
    referer,
):
    ranked = []

    for candidate in candidates:
        candidate = dict(
            candidate
        )

        candidate[
            "score"
        ] = candidate_score(
            candidate,
            keywords,
        )

        ranked.append(
            candidate
        )

    ranked.sort(
        key=lambda item: item[
            "score"
        ],
        reverse=True,
    )

    validated = []

    for candidate in ranked[:20]:
        probe = probe_image(
            candidate[
                "url"
            ],
            timeout,
            referer,
        )

        if not probe:
            continue

        candidate.update({
            "validated_width": probe[
                "width"
            ],
            "validated_height": probe[
                "height"
            ],
            "format": probe[
                "format"
            ],
            "content_type": probe[
                "content_type"
            ],
        })

        if (
            probe[
                "width"
            ] >= 1920
            and probe[
                "height"
            ] >= 1080
        ):
            candidate[
                "score"
            ] += 30

        elif (
            probe[
                "width"
            ] >= 1200
            and probe[
                "height"
            ] >= 630
        ):
            candidate[
                "score"
            ] += 20

        elif (
            probe[
                "width"
            ] >= 800
            and probe[
                "height"
            ] >= 450
        ):
            candidate[
                "score"
            ] += 10

        validated.append(
            candidate
        )

    validated.sort(
        key=lambda item: item[
            "score"
        ],
        reverse=True,
    )

    return validated


# =========================================================
# FUENTES / QUERIES ALTERNATIVAS
# =========================================================

def source_name_from_entry(
    entry,
    url,
):
    try:
        if getattr(
            entry,
            "source",
            None,
        ):
            title = getattr(
                entry.source,
                "title",
                "",
            )

            if title:
                return str(
                    title
                )

    except Exception:
        pass

    return (
        domain(
            url
        ).replace(
            "www.",
            "",
        )
        or "FUENTE WEB"
    )


def derive_search_queries(
    title,
    source,
    article_url,
):
    clean = clean_title(
        title,
        source,
    )

    queries = [
        clean
    ]

    distinctive = (
        distinctive_title_tokens(
            clean,
            source,
        )
    )

    # Slug de artículo.
    url_words = [
        word
        for word in re.findall(
            r"[a-z0-9]+",
            normalize(
                urlparse(
                    article_url
                ).path.replace(
                    "-",
                    " ",
                )
            ),
        )
        if (
            len(word) >= 3
            and word not in STOPWORDS
        )
    ]

    useful_slug = [
        word
        for word in url_words
        if word not in GENERIC_WORDS
    ]

    if useful_slug:
        queries.append(
            " ".join(
                useful_slug[:8]
            )
        )

    # V4.2: consultas cortas por entidades distintivas.
    # Ej:
    # nvidia mediatek
    # wingfeather saga
    # pokemon wild card
    if len(
        distinctive
    ) >= 2:
        queries.append(
            " ".join(
                distinctive[:2]
            )
        )

    if len(
        distinctive
    ) >= 3:
        queries.append(
            " ".join(
                distinctive[:3]
            )
        )

    if len(
        distinctive
    ) >= 5:
        queries.append(
            " ".join(
                distinctive[:5]
            )
        )

    output = []

    for query in queries:
        query = (
            query.strip()
        )

        if (
            query
            and query not in output
        ):
            output.append(
                query
            )

    return output[:5]


def google_news_alternatives(
    title,
    source,
    article_url,
    limit_per_query=7,
):
    results = []
    seen = set()

    for query in derive_search_queries(
        title,
        source,
        article_url,
    ):
        try:
            response = requests.get(
                "https://news.google.com/rss/search",
                params={
                    "q": query,
                    "hl": "en-US",
                    "gl": "US",
                    "ceid": "US:en",
                },
                headers=HEADERS,
                timeout=15,
            )

            response.raise_for_status()

            feed = feedparser.parse(
                response.content
            )

        except Exception:
            continue

        for entry in feed.entries[
            :limit_per_query
        ]:
            link = getattr(
                entry,
                "link",
                "",
            )

            if not link:
                continue

            real = resolve_google_news(
                link
            )

            if (
                not real
                or real in seen
            ):
                continue

            seen.add(
                real
            )

            source_name = (
                source_name_from_entry(
                    entry,
                    real,
                )
            )

            results.append({
                "url": real,
                "source": source_name,
                "title": getattr(
                    entry,
                    "title",
                    "",
                ),
                "quality_bonus": source_quality_bonus(
                    source_name,
                    real,
                ),
            })

    # V4.2: fuentes más confiables primero.
    results.sort(
        key=lambda item: item[
            "quality_bonus"
        ],
        reverse=True,
    )

    return results[:18]


def bing_news_alternatives(
    title,
    source,
    article_url,
    limit_per_query=5,
):
    """
    Fallback gratuito adicional.
    Bing News ofrece RSS y puede devolver coberturas que Google News no mostró.
    """
    results = []
    seen = set()

    for query in derive_search_queries(
        title,
        source,
        article_url,
    )[:3]:
        try:
            response = requests.get(
                "https://www.bing.com/news/search",
                params={
                    "q": query,
                    "format": "rss",
                },
                headers=HEADERS,
                timeout=15,
            )

            response.raise_for_status()

            feed = feedparser.parse(
                response.content
            )

        except Exception:
            continue

        for entry in feed.entries[
            :limit_per_query
        ]:
            link = getattr(
                entry,
                "link",
                "",
            )

            if (
                not link
                or link in seen
            ):
                continue

            seen.add(
                link
            )

            source_name = (
                source_name_from_entry(
                    entry,
                    link,
                )
            )

            results.append({
                "url": link,
                "source": source_name,
                "title": getattr(
                    entry,
                    "title",
                    "",
                ),
                "quality_bonus": source_quality_bonus(
                    source_name,
                    link,
                ),
            })

    results.sort(
        key=lambda item: item[
            "quality_bonus"
        ],
        reverse=True,
    )

    return results[:12]


# =========================================================
# EVALUAR ARTÍCULO
# =========================================================

def winner_is_acceptable(
    winner,
    source_name,
    article_url,
    is_original,
):
    quality_bonus = source_quality_bonus(
        source_name,
        article_url,
    )

    winner[
        "source_quality_bonus"
    ] = quality_bonus

    winner[
        "score_with_source"
    ] = (
        winner[
            "score"
        ]
        + quality_bonus
    )

    url_specific = winner.get(
        "matched_url_specific",
        [],
    )

    text_specific = winner.get(
        "matched_text_specific",
        [],
    )

    bad_url_terms = winner.get(
        "bad_url_terms",
        [],
    )

    if bad_url_terms:
        return False

    # Caso ideal.
    if (
        winner[
            "score_with_source"
        ] >= 105
        and url_specific
    ):
        return True

    # V4.2:
    # Original article + OG/JSON-LD grande + contexto textual del propio artículo.
    if (
        is_original
        and winner[
            "score_with_source"
        ] >= 90
        and len(
            text_specific
        ) >= 2
        and winner[
            "validated_width"
        ] >= 1000
        and winner[
            "validated_height"
        ] >= 560
    ):
        return True

    # Fuente oficial/premium: permitimos CDN filename genérico si
    # el ALT/título coincide con al menos 2 términos específicos.
    if (
        quality_bonus >= 30
        and winner[
            "score_with_source"
        ] >= 95
        and len(
            text_specific
        ) >= 2
        and winner[
            "validated_width"
        ] >= 1000
    ):
        return True

    # Fuentes buenas: un poco más exigente.
    if (
        quality_bonus >= 15
        and winner[
            "score_with_source"
        ] >= 110
        and len(
            text_specific
        ) >= 2
    ):
        return True

    return False


def evaluate_article(
    article_url,
    source_name,
    keywords,
    timeout,
    browser_fallback,
    is_original=False,
):
    try:
        final_url, html = fetch_article(
            article_url,
            timeout,
            browser_fallback,
        )

    except Exception:
        return None

    candidates = collect_candidates(
        html,
        final_url,
    )

    if not candidates:
        return None

    validated = rank_and_validate(
        candidates,
        keywords,
        timeout,
        final_url,
    )

    if not validated:
        return None

    # Revisar varios candidatos, no solo el primero.
    for winner in validated[:6]:
        if winner_is_acceptable(
            winner,
            source_name,
            final_url,
            is_original,
        ):
            return {
                "winner": winner,
                "alternatives": validated[:5],
                "resolved_article_url": final_url,
                "source": (
                    source_name
                    or domain(
                        final_url
                    ).replace(
                        "www.",
                        "",
                    )
                ),
                "source_quality_bonus": (
                    source_quality_bonus(
                        source_name,
                        final_url,
                    )
                ),
            }

    return None


# =========================================================
# RESOLVER UNA NOTICIA
# =========================================================

def resolve_one(
    item,
    index,
    timeout,
):
    original_url = str(
        item.get(
            "url",
            "",
        )
    ).strip()

    source = str(
        item.get(
            "fuente",
            "",
        )
    ).strip()

    title = str(
        item.get(
            "titulo",
            "",
        )
    ).strip()

    result = {
        "numero": item.get(
            "numero",
            f"{index:02d}",
        ),
        "titulo": title,
        "source": source,
        "article_url": original_url,
        "resolved_article_url": "",
        "image_candidate_url": "",
        "image_source": "",
        "image_source_url": "",
        "source_type": "",
        "relevance_score": 0,
        "source_quality_bonus": 0,
        "validated_width": 0,
        "validated_height": 0,
        "selection_origin": "",
        "alternatives": [],
        "status": "",
    }

    if not original_url:
        result[
            "status"
        ] = "NO_ARTICLE_URL"

        return result

    real_url = resolve_google_news(
        original_url
    )

    if not real_url:
        result[
            "status"
        ] = "URL_NOT_RESOLVED"

        return result

    print(
        "    URL real:",
        real_url,
    )

    keywords = topic_keywords(
        title,
        source,
        real_url,
    )

    # -----------------------------------------------------
    # 1. ARTÍCULO ORIGINAL
    # -----------------------------------------------------

    print(
        "    Buscando en artículo original..."
    )

    original = evaluate_article(
        real_url,
        source,
        keywords,
        timeout,
        browser_fallback=True,
        is_original=True,
    )

    if original:
        winner = original[
            "winner"
        ]

        result.update({
            "resolved_article_url": original[
                "resolved_article_url"
            ],
            "image_candidate_url": winner[
                "url"
            ],
            "image_source": original[
                "source"
            ],
            "image_source_url": original[
                "resolved_article_url"
            ],
            "source_type": winner[
                "kind"
            ],
            "relevance_score": winner[
                "score_with_source"
            ],
            "source_quality_bonus": original[
                "source_quality_bonus"
            ],
            "validated_width": winner[
                "validated_width"
            ],
            "validated_height": winner[
                "validated_height"
            ],
            "selection_origin": "ORIGINAL_ARTICLE",
            "alternatives": original[
                "alternatives"
            ],
            "status": "IMAGE_CANDIDATE_FOUND",
        })

        return result

    print(
        "    Artículo original sin imagen adecuada."
    )

    # -----------------------------------------------------
    # 2. GOOGLE NEWS
    # -----------------------------------------------------

    print(
        "    Buscando coberturas alternativas en Google News..."
    )

    original_domain = domain(
        real_url
    )

    best = None
    all_alts = []

    google_alts = google_news_alternatives(
        title,
        source,
        real_url,
        limit_per_query=7,
    )

    for alternative in google_alts:
        if domain(
            alternative[
                "url"
            ]
        ) == original_domain:
            continue

        checked = evaluate_article(
            alternative[
                "url"
            ],
            alternative[
                "source"
            ],
            keywords,
            timeout,
            browser_fallback=False,
            is_original=False,
        )

        if not checked:
            continue

        winner = checked[
            "winner"
        ]

        all_alts.append({
            "source": checked[
                "source"
            ],
            "article_url": checked[
                "resolved_article_url"
            ],
            **winner,
        })

        if (
            best is None
            or winner[
                "score_with_source"
            ]
            > best[
                "winner"
            ][
                "score_with_source"
            ]
        ):
            best = checked

    # -----------------------------------------------------
    # 3. BING NEWS FALLBACK
    # -----------------------------------------------------

    if best is None:
        print(
            "    Google News sin resultado suficiente."
        )

        print(
            "    Probando fallback gratuito en Bing News..."
        )

        for alternative in bing_news_alternatives(
            title,
            source,
            real_url,
            limit_per_query=5,
        ):
            if domain(
                alternative[
                    "url"
                ]
            ) == original_domain:
                continue

            checked = evaluate_article(
                alternative[
                    "url"
                ],
                alternative[
                    "source"
                ],
                keywords,
                timeout,
                browser_fallback=False,
                is_original=False,
            )

            if not checked:
                continue

            winner = checked[
                "winner"
            ]

            all_alts.append({
                "source": checked[
                    "source"
                ],
                "article_url": checked[
                    "resolved_article_url"
                ],
                **winner,
            })

            if (
                best is None
                or winner[
                    "score_with_source"
                ]
                > best[
                    "winner"
                ][
                    "score_with_source"
                ]
            ):
                best = checked

    all_alts.sort(
        key=lambda item: item.get(
            "score_with_source",
            item.get(
                "score",
                0,
            ),
        ),
        reverse=True,
    )

    result[
        "alternatives"
    ] = all_alts[:5]

    if best:
        winner = best[
            "winner"
        ]

        result.update({
            "resolved_article_url": real_url,
            "image_candidate_url": winner[
                "url"
            ],
            "image_source": best[
                "source"
            ],
            "image_source_url": best[
                "resolved_article_url"
            ],
            "source_type": (
                "alternative_"
                + winner[
                    "kind"
                ]
            ),
            "relevance_score": winner[
                "score_with_source"
            ],
            "source_quality_bonus": best[
                "source_quality_bonus"
            ],
            "validated_width": winner[
                "validated_width"
            ],
            "validated_height": winner[
                "validated_height"
            ],
            "selection_origin": "ALTERNATIVE_COVERAGE",
            "status": "IMAGE_CANDIDATE_FOUND",
        })

        return result

    result[
        "resolved_article_url"
    ] = real_url

    result[
        "status"
    ] = "NO_RELEVANT_IMAGE_FOUND"

    return result


# =========================================================
# MAIN
# =========================================================

def main():
    config = (
        json.loads(
            CONFIG_FILE.read_text(
                encoding="utf-8"
            )
        )
        if CONFIG_FILE.exists()
        else {}
    )

    timeout = int(
        config.get(
            "request_timeout_seconds",
            15,
        )
    )

    news = json.loads(
        NEWS_FILE.read_text(
            encoding="utf-8"
        )
    )

    results = []

    found = 0
    unresolved = 0

    print()
    print("=" * 60)
    print(" RESOLVIENDO IMÁGENES V4.2")
    print("=" * 60)
    print()

    for index, item in enumerate(
        news,
        start=1,
    ):
        print(
            f'{index:02d}. '
            f'{item.get("titulo", "")[:75]}'
        )

        result = resolve_one(
            item,
            index,
            timeout,
        )

        results.append(
            result
        )

        if (
            result[
                "status"
            ]
            == "IMAGE_CANDIDATE_FOUND"
        ):
            found += 1

            print(
                "    Imagen seleccionada:"
            )

            print(
                "   ",
                result[
                    "image_candidate_url"
                ],
            )

            print(
                "    Origen:",
                result[
                    "selection_origin"
                ],
            )

            print(
                "    Tipo:",
                result[
                    "source_type"
                ],
            )

            print(
                "    Relevancia:",
                result[
                    "relevance_score"
                ],
            )

            print(
                "    Bonus fuente:",
                result[
                    "source_quality_bonus"
                ],
            )

            print(
                "    Resolución:",
                (
                    f'{result["validated_width"]}'
                    f'x{result["validated_height"]}'
                ),
            )

            print(
                "    Fuente:",
                result[
                    "image_source"
                ],
            )

        else:
            unresolved += 1

            print(
                "    SIN IMAGEN ACEPTABLE"
            )

            print(
                "    Estado:",
                result[
                    "status"
                ],
            )

        print()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 60)
    print(" RESULTADO")
    print("=" * 60)

    print(
        "Imágenes aceptadas:",
        found,
    )

    print(
        "Sin resolver:",
        unresolved,
    )

    print(
        "Costo API: $0.00"
    )

    print()


if __name__ == "__main__":
    main()
