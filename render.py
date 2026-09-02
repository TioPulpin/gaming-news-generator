import json
from pathlib import Path
from playwright.sync_api import sync_playwright

# =========================================================
# RUTAS DEL PROYECTO
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

TEMPLATE_FILE = BASE_DIR / "template" / "index.html"
DATA_FILE = BASE_DIR / "data" / "noticia.json"
OUTPUT_FILE = BASE_DIR / "output" / "01_project_helix.png"

AVATAR_FILE = BASE_DIR / "assets" / "avatar.png"


# =========================================================
# FUNCIÓN PARA CONVERTIR ARCHIVOS LOCALES EN URL
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


# =========================================================
# LEER DATOS DE LA NOTICIA
# =========================================================

data = json.loads(
    DATA_FILE.read_text(encoding="utf-8")
)


# =========================================================
# PREPARAR DATOS PARA LA PLANTILLA
# =========================================================

payload = {
    "numero": data.get("numero", "01"),

    "categoria": data.get(
        "categoria",
        "INDUSTRIA"
    ),

    "fecha": data.get(
        "fecha",
        ""
    ),

    "titulo": data.get(
        "titulo",
        ""
    ),    "tituloDestacado": data.get(
        "tituloDestacado",
        []
    ),

    "resumen": data.get(
        "resumen",
        ""
    ),

    "resumenDestacado": data.get(
        "resumenDestacado",
        []
    ),

    "imagen": file_uri(
        data.get("imagen", "")
    ),

    "avatar": (
        AVATAR_FILE.resolve().as_uri()
        if AVATAR_FILE.exists()
        else ""
    )
}


# =========================================================
# JAVASCRIPT QUE RELLENA LA PLANTILLA
# =========================================================

render_script = r"""
(payload) => {

    function escapeRegExp(text) {
        return text.replace(
            /[.*+?^${}()|[\]\\]/g,
            '\\$&'
        );
    }

    function applyHighlights(text, words) {

        let result = text || '';

        for (const word of (words || [])) {

            if (!word) {
                continue;
            }

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
    document.getElementById('headline').innerHTML =
        applyHighlights(
            payload.titulo,
            payload.tituloDestacado
        );

    // -------------------------
    // RESUMEN
    // -------------------------

    document.getElementById('summary').innerHTML =
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

    const headlineElement =
        document.getElementById('headline');

    const summaryElement =
        document.getElementById('summary');

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
# GENERAR PNG
# =========================================================

with sync_playwright() as p:

    browser = p.chromium.launch()

    page = browser.new_page(
        viewport={
            "width": 1080,
            "height": 1350
        },
        device_scale_factor=1
    )

    page.goto(
        TEMPLATE_FILE.resolve().as_uri()
    )

    page.evaluate(
        render_script,
        payload
    )

    # Esperamos un poco para que las imágenes carguen
    page.wait_for_timeout(1000)

    page.locator("#card").screenshot(
        path=str(OUTPUT_FILE)
    )

    browser.close()


print()
print("============================================")
print(" GAMING NEWS GENERATOR")
print("============================================")
print()
print(f"Imagen generada correctamente:")
print(OUTPUT_FILE)
print()