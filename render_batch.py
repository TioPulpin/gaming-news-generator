import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

# =========================================================
# RUTAS DEL PROYECTO
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

TEMPLATE_FILE = BASE_DIR / "template" / "index.html"
DATA_FILE = BASE_DIR / "data" / "noticias.json"
OUTPUT_DIR = BASE_DIR / "output"

AVATAR_FILE = BASE_DIR / "assets" / "avatar.png"


# =========================================================
# UTILIDADES
# =========================================================

def file_uri(relative_path: str) -> str:
    if not relative_path:
        return ""

    path = Path(relative_path)

    if not path.is_absolute():
        path = BASE_DIR / path

    path = path.resolve()

    if not path.exists():
        print(f"ADVERTENCIA: No se encontró el archivo: {path}")
        return ""

    return path.as_uri()


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "_", text)
    text = text.strip("_")
    return text or "noticia"


def build_payload(item: dict) -> dict:
    return {
    "numero": item.get("numero", "01"),
    "categoria": item.get("categoria", "INDUSTRIA"),
    "fecha": item.get("fecha", ""),
    "titulo": item.get("titulo", ""),
    "tituloDestacado": item.get("tituloDestacado", []),
    "resumen": item.get("resumen", ""),
    "resumenDestacado": item.get("resumenDestacado", []),
    "imagen": file_uri(item.get("imagen", "")),
    "imagenFuente": item.get("imagenFuente", ""),
    "avatar": AVATAR_FILE.resolve().as_uri() if AVATAR_FILE.exists() else ""
}


# =========================================================
# SCRIPT JS PARA RELLENAR LA PLANTILLA
# =========================================================

render_script = r"""
(payload) => {

    function escapeRegExp(text) {
        return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function applyHighlights(text, words) {
        let result = text || '';

        for (const word of (words || [])) {
            if (!word) continue;

            const regex = new RegExp(
                escapeRegExp(word),
                'gi'
            );

            result = result.replace(
                regex,
                '<span class="highlight">$&</span>'
            );
        }

        return result;
    }

    // -------------------------
    // NÚMERO
    // -------------------------

    document.getElementById('number').textContent =
        payload.numero || '01';

    // -------------------------
    // CATEGORÍA
    // -------------------------

    const categoryElement =
        document.getElementById('category');

    if (categoryElement) {
        categoryElement.textContent =
            payload.categoria || 'INDUSTRIA';
    }

    // -------------------------
    // FECHA
    // -------------------------

    const dateElement =
        document.getElementById('news-date');

    if (dateElement) {
        dateElement.textContent =
            payload.fecha || '';
    }

    // -------------------------
    // TITULAR
    // -------------------------

    const headlineElement =
        document.getElementById('headline');

    headlineElement.innerHTML =
        applyHighlights(
            payload.titulo,
            payload.tituloDestacado
        );

    // -------------------------
    // RESUMEN
    // -------------------------

    const summaryElement =
        document.getElementById('summary');

    summaryElement.innerHTML =
        applyHighlights(
            payload.resumen,
            payload.resumenDestacado
        );

    // -------------------------
    // IMAGEN PRINCIPAL
    // -------------------------

    const mainImage =
        document.getElementById('main-image');

    const placeholder =
        document.getElementById('image-placeholder');

    if (payload.imagen) {
        mainImage.src = payload.imagen;
        mainImage.style.display = 'block';
        placeholder.style.display = 'none';
    } else {
        mainImage.removeAttribute('src');
        mainImage.style.display = 'none';
        placeholder.style.display = 'flex';
    }

    // -------------------------
    // FUENTE DE IMAGEN
    // -------------------------

    const imageSource =
        document.getElementById('image-source');

    if (imageSource) {

        if (payload.imagenFuente) {

            imageSource.innerHTML =
                '<strong>FUENTE DE IMAGEN:</strong> '
                + payload.imagenFuente;

            imageSource.style.display = 'block';

        } else {

            imageSource.innerHTML = '';

            imageSource.style.display = 'none';
        }
    }

    // -------------------------
    // AVATAR
    // -------------------------

    const avatarImage =
        document.getElementById('avatar-image');

    const avatarFallback =
        document.getElementById('avatar-fallback');

    if (avatarImage && avatarFallback) {
        if (payload.avatar) {
            avatarImage.src = payload.avatar;
            avatarImage.style.display = 'block';
            avatarFallback.style.display = 'none';
        } else {
            avatarImage.removeAttribute('src');
            avatarImage.style.display = 'none';
            avatarFallback.style.display = 'flex';
        }
    }

    // -------------------------
    // AJUSTE AUTOMÁTICO DE TAMAÑO
    // -------------------------

    const headlineLength =
        (headlineElement.textContent || '').trim().length;

    if (headlineLength <= 34) {
        headlineElement.style.fontSize = '76px';
        headlineElement.style.lineHeight = '0.91';
    } else if (headlineLength <= 52) {
        headlineElement.style.fontSize = '70px';
        headlineElement.style.lineHeight = '0.91';
    } else if (headlineLength <= 68) {
        headlineElement.style.fontSize = '64px';
        headlineElement.style.lineHeight = '0.93';
    } else {
        headlineElement.style.fontSize = '58px';
        headlineElement.style.lineHeight = '0.95';
    }

    const summaryLength =
        (summaryElement.textContent || '').trim().length;

    if (summaryLength <= 120) {
        summaryElement.style.fontSize = '34px';
        summaryElement.style.lineHeight = '1.23';
    } else if (summaryLength <= 170) {
        summaryElement.style.fontSize = '31px';
        summaryElement.style.lineHeight = '1.24';
    } else {
        summaryElement.style.fontSize = '28px';
        summaryElement.style.lineHeight = '1.26';
    }
}
"""


# =========================================================
# CARGAR DATOS
# =========================================================

items = json.loads(DATA_FILE.read_text(encoding="utf-8"))

if not isinstance(items, list):
    raise ValueError("data/noticias.json debe contener una lista de noticias.")

OUTPUT_DIR.mkdir(exist_ok=True)


# =========================================================
# RENDER EN LOTE
# =========================================================

with sync_playwright() as p:
    browser = p.chromium.launch()

    page = browser.new_page(
        viewport={"width": 1080, "height": 1350},
        device_scale_factor=1
    )

    page.goto(TEMPLATE_FILE.resolve().as_uri())

    generated_files = []

    for item in items:
        payload = build_payload(item)

        page.evaluate(render_script, payload)
        page.wait_for_timeout(900)

        numero = payload.get("numero", "00")
        titulo = payload.get("titulo", "noticia")
        filename = f"{numero}_{slugify(titulo)[:50]}.png"
        output_path = OUTPUT_DIR / filename

        page.locator("#card").screenshot(path=str(output_path))
        generated_files.append(output_path)

        print(f"Generado: {output_path.name}")

    browser.close()

print()
print("============================================")
print(" GAMING NEWS GENERATOR - LOTE")
print("============================================")
print()

for item in generated_files:
    print(item)

print()
print(f"Total de imágenes generadas: {len(generated_files)}")
print()
