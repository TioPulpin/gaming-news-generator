import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent

NEWS_FILE = BASE_DIR / "data" / "noticias.json"
IMAGE_CANDIDATES_FILE = BASE_DIR / "data" / "image_candidates.json"
OUTPUT_FILE = BASE_DIR / "data" / "article_context.json"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
}


def clean_text(text):
    text = str(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_description(soup):
    selectors = [
        ("meta", {"property": "og:description"}),
        ("meta", {"name": "description"}),
        ("meta", {"name": "twitter:description"}),
    ]

    for tag_name, attrs in selectors:
        tag = soup.find(tag_name, attrs=attrs)

        if not tag:
            continue

        content = clean_text(
            tag.get("content", "")
        )

        if content:
            return content

    return ""


def extract_title(soup):
    selectors = [
        ("meta", {"property": "og:title"}),
        ("meta", {"name": "twitter:title"}),
    ]

    for tag_name, attrs in selectors:
        tag = soup.find(tag_name, attrs=attrs)

        if not tag:
            continue

        content = clean_text(
            tag.get("content", "")
        )

        if content:
            return content

    h1 = soup.find("h1")

    if h1:
        title = clean_text(
            h1.get_text(" ", strip=True)
        )

        if title:
            return title

    if soup.title:
        return clean_text(
            soup.title.get_text(" ", strip=True)
        )

    return ""


def extract_article_text(soup):
    article = (
        soup.find("article")
        or soup.find("main")
        or soup
    )

    paragraphs = []
    seen = set()

    for p in article.find_all("p", limit=35):
        text = clean_text(
            p.get_text(" ", strip=True)
        )

        if len(text) < 50:
            continue

        key = text.lower()

        if key in seen:
            continue

        seen.add(key)
        paragraphs.append(text)

        if len(paragraphs) >= 8:
            break

    return paragraphs


def parse_article(final_url, html):
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    article_title = extract_title(soup)
    description = extract_description(soup)
    paragraphs = extract_article_text(soup)

    extracto = clean_text(
        " ".join(paragraphs[:3])
    )

    return {
        "url_real": final_url,
        "titulo_original": article_title,
        "descripcion": description,
        "extracto": extracto,
        "parrafos": paragraphs[:5],
    }


def fetch_with_requests(url, timeout=20):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=timeout,
        allow_redirects=True
    )

    response.raise_for_status()

    return (
        response.url,
        response.text
    )


def fetch_with_browser(url):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            viewport={
                "width": 1440,
                "height": 1000
            },
            user_agent=HEADERS["User-Agent"],
            locale="en-US"
        )

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            page.wait_for_timeout(1800)

            return (
                page.url,
                page.content()
            )

        finally:
            browser.close()


def try_article(url, allow_browser=True):
    if not url:
        return None, "SIN_URL"

    try:
        final_url, html = fetch_with_requests(url)
        return parse_article(final_url, html), "REQUESTS"

    except Exception as requests_exc:
        if not allow_browser:
            return None, f"REQUESTS_ERROR: {requests_exc}"

        try:
            final_url, html = fetch_with_browser(url)
            return parse_article(final_url, html), "BROWSER"

        except Exception as browser_exc:
            return (
                None,
                (
                    f"REQUESTS_ERROR: {requests_exc} | "
                    f"BROWSER_ERROR: {browser_exc}"
                )
            )


def has_useful_context(article):
    if not article:
        return False

    if article.get("extracto"):
        return True

    if article.get("descripcion"):
        return True

    if article.get("titulo_original"):
        return True

    return False


def main():
    news = json.loads(
        NEWS_FILE.read_text(
            encoding="utf-8"
        )
    )

    if IMAGE_CANDIDATES_FILE.exists():
        image_candidates = json.loads(
            IMAGE_CANDIDATES_FILE.read_text(
                encoding="utf-8"
            )
        )
    else:
        image_candidates = []

    image_map = {
        item.get("numero"): item
        for item in image_candidates
    }

    results = []

    print()
    print("=" * 60)
    print(" ENRIQUECIENDO ARTÍCULOS V2")
    print("=" * 60)
    print()

    for item in news:
        numero = item.get("numero", "")
        titulo = item.get("titulo", "")
        fuente = item.get("fuente", "")
        image_info = image_map.get(
            numero,
            {}
        )

        original_url = (
            image_info.get("resolved_article_url")
            or item.get("url", "")
        )

        fallback_url = (
            image_info.get("image_source_url")
            or ""
        )

        fallback_source = (
            image_info.get("image_source")
            or ""
        )

        print(
            f"{numero}. {titulo[:70]}"
        )

        result = {
            "numero": numero,
            "fuente": fuente,
            "url_original": item.get("url", ""),
            "url_real": original_url,
            "titulo_original": "",
            "descripcion": "",
            "extracto": "",
            "parrafos": [],
            "context_source": fuente,
            "context_origin": "",
            "fallback_url": fallback_url,
            "estado": "",
            "detalle": ""
        }

        # =================================================
        # INTENTO 1: ARTÍCULO ORIGINAL
        # =================================================

        article, method = try_article(
            original_url,
            allow_browser=True
        )

        if has_useful_context(article):
            result.update(article)
            result["context_source"] = fuente
            result["context_origin"] = (
                "ORIGINAL_ARTICLE_" + method
            )
            result["estado"] = "OK"

            print("    OK - artículo original")
            print(
                "    Método:",
                method
            )
            print(
                "    Título:",
                result["titulo_original"][:90]
            )
            print()

            results.append(result)
            continue

        # =================================================
        # INTENTO 2: COBERTURA ALTERNATIVA USADA PARA IMAGEN
        # =================================================

        if (
            fallback_url
            and fallback_url != original_url
        ):
            print(
                "    Original no accesible o sin contexto."
            )
            print(
                "    Probando cobertura alternativa..."
            )

            article, fallback_method = try_article(
                fallback_url,
                allow_browser=True
            )

            if has_useful_context(article):
                result.update(article)
                result["context_source"] = (
                    fallback_source
                    or fuente
                )
                result["context_origin"] = (
                    "ALTERNATIVE_COVERAGE_"
                    + fallback_method
                )
                result["estado"] = "OK"

                print("    OK - cobertura alternativa")
                print(
                    "    Fuente de contexto:",
                    result["context_source"]
                )
                print(
                    "    Método:",
                    fallback_method
                )
                print(
                    "    Título:",
                    result["titulo_original"][:90]
                )
                print()

                results.append(result)
                continue

        # =================================================
        # FALLBACK FINAL:
        # USAR LOS DATOS QUE YA TENEMOS
        # =================================================

        result["titulo_original"] = titulo

        result["descripcion"] = (
            "Contexto limitado. "
            "No se pudo extraer el artículo completo."
        )

        result["context_origin"] = (
            "RSS_FALLBACK"
        )

        result["estado"] = (
            "PARCIAL"
        )

        result["detalle"] = method

        print(
            "    PARCIAL - se usará el titular RSS."
        )
        print()

        results.append(result)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    ok_count = sum(
        1
        for x in results
        if x.get("estado") == "OK"
    )

    partial_count = sum(
        1
        for x in results
        if x.get("estado") == "PARCIAL"
    )

    print("=" * 60)
    print(" RESULTADO")
    print("=" * 60)
    print()
    print(
        "Artículos con contexto completo:",
        ok_count
    )
    print(
        "Contexto parcial:",
        partial_count
    )
    print(
        "Total:",
        len(results)
    )
    print(
        "Archivo generado:",
        OUTPUT_FILE
    )
    print(
        "Costo API: $0.00"
    )
    print()


if __name__ == "__main__":
    main()
