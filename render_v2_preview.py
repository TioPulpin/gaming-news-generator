import json
from pathlib import Path

from playwright.sync_api import sync_playwright


# =========================================================
# RUTAS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

TEMPLATE_FILE = (
    BASE_DIR
    / "template_v2"
    / "index.html"
)

DATA_FILE = (
    BASE_DIR
    / "data"
    / "noticias.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "output"
    / "preview_template_v2.png"
)

AVATAR_FILE = (
    BASE_DIR
    / "assets"
    / "avatar.png"
)


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
        print(
            "ADVERTENCIA: archivo no encontrado:"
        )
        print(path)
        return ""

    return path.as_uri()



def fold_text(text: str) -> str:
    import unicodedata

    text = str(text or "")

    return (
        unicodedata
        .normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


def shorten(
    text: str,
    limit: int = 92,
) -> str:

    text = " ".join(
        str(text or "").split()
    )

    if len(text) <= limit:
        return text

    cut = text[:limit].rsplit(
        " ",
        1,
    )[0]

    return cut.rstrip(
        " ,.;:"
    ) + "."


def extract_date(text: str) -> str:
    import re

    pattern = (
        r"\b"
        r"(?:\d{1,2}\s+de\s+)?"
        r"(?:enero|febrero|marzo|abril|mayo|junio|"
        r"julio|agosto|septiembre|octubre|noviembre|diciembre)"
        r"\s+de\s+20\d{2}"
        r"\b"
    )

    match = re.search(
        pattern,
        str(text or ""),
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(0)

    year = re.search(
        r"\b20\d{2}\b",
        str(text or ""),
    )

    if year:
        return year.group(0)

    return ""


def extract_amount(text: str) -> str:
    import re

    match = re.search(
        (
            r"\b"
            r"\d[\d\.,]*"
            r"\s+"
            r"(?:millones|mil\s+millones)"
            r"\s+de\s+d(?:o|\u00f3)lares"
            r"\b"
        ),
        str(text or ""),
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(0)

    return ""


def extract_platforms(text: str) -> list[str]:

    folded = fold_text(
        text
    )

    possible = [
        (
            "Nintendo Switch 2",
            "nintendo switch 2",
        ),
        (
            "PlayStation",
            "playstation",
        ),
        (
            "Xbox",
            "xbox",
        ),
        (
            "PC",
            " pc ",
        ),
        (
            "Crunchyroll",
            "crunchyroll",
        ),
        (
            "Prime Video",
            "prime video",
        ),
        (
            "Netflix",
            "netflix",
        ),
        (
            "Disney+",
            "disney+",
        ),
    ]

    padded = (
        " "
        + folded
        + " "
    )

    found = []

    for label, needle in possible:
        if needle in padded:
            found.append(
                label
            )

    return found


def build_modules(
    item: dict,
) -> list[dict]:

    # =====================================================
    # MODULOS EDITORIALES GENERADOS POR TERRA
    # =====================================================

    provided = item.get(
        "modulos"
    )

    if (
        isinstance(provided, list)
        and len(provided) == 3
    ):
        normalized = []

        for module in provided:
            if not isinstance(
                module,
                dict,
            ):
                normalized = []
                break

            title = str(
                module.get(
                    "titulo",
                    "",
                )
            ).strip()

            value = str(
                module.get(
                    "texto",
                    "",
                )
            ).strip()

            if (
                not title
                or not value
            ):
                normalized = []
                break

            normalized.append({
                "titulo": title,
                "texto": value,
            })

        if len(normalized) == 3:
            return normalized


    # =====================================================
    # FALLBACK LOCAL
    # =====================================================

    titulo = str(
        item.get(
            "titulo",
            "",
        )
    )

    resumen = str(
        item.get(
            "resumen",
            "",
        )
    )

    angulo = str(
        item.get(
            "anguloShort",
            "",
        )
    )

    importa = str(
        item.get(
            "por_que_importa",
            "",
        )
    )

    categoria = str(
        item.get(
            "categoria",
            "",
        )
    )

    corpus = " ".join([
        titulo,
        resumen,
        angulo,
        importa,
        categoria,
    ])

    folded = fold_text(
        corpus
    )

    date_value = extract_date(
        corpus
    )

    amount_value = extract_amount(
        corpus
    )

    platforms = extract_platforms(
        corpus
    )

    # =====================================================
    # MODULO 1
    # =====================================================

    if (
        "inviert" in folded
        or "inversion" in folded
    ) and amount_value:

        module_1 = {
            "titulo": "INVERSI\u00d3N",
            "texto": amount_value,
        }

    elif (
        "retras" in folded
        or "aplaz" in folded
    ) and date_value:

        module_1 = {
            "titulo": "FECHA",
            "texto": date_value,
        }

    elif (
        "nintendo switch 2"
        in folded
    ):

        module_1 = {
            "titulo": "PLATAFORMA",
            "texto": "Nintendo Switch 2",
        }

    elif (
        "pelicula" in folded
        and date_value
    ):

        module_1 = {
            "titulo": "LANZAMIENTO",
            "texto": date_value,
        }

    elif (
        "ciberataque" in folded
        or "hackeo" in folded
        or "robo de datos" in folded
    ):

        module_1 = {
            "titulo": "QU\u00c9 CAMBIA",
            "texto": shorten(
                angulo
                or resumen,
                88,
            ),
        }

    elif (
        "semanal" in folded
        or "cada semana" in folded
    ):

        module_1 = {
            "titulo": "DISPONIBILIDAD",
            "texto": shorten(
                angulo
                or resumen,
                88,
            ),
        }

    else:

        module_1 = {
            "titulo": "CONTEXTO",
            "texto": shorten(
                categoria,
                72,
            ),
        }


    # =====================================================
    # MODULO 2
    # =====================================================

    module_2 = {
        "titulo": "POR QU\u00c9 IMPORTA",
        "texto": shorten(
            importa
            or angulo
            or resumen,
            96,
        ),
    }


    # =====================================================
    # MODULO 3
    # =====================================================

    if (
        "nvlink fusion"
        in folded
    ):

        module_3 = {
            "titulo": "TECNOLOG\u00cdA",
            "texto": "NVLink Fusion",
        }

    elif (
        date_value
        and module_1["titulo"]
        not in {
            "FECHA",
            "LANZAMIENTO",
        }
    ):

        module_3 = {
            "titulo": "FECHA",
            "texto": date_value,
        }

    elif (
        platforms
        and module_1["titulo"]
        != "PLATAFORMA"
    ):

        module_3 = {
            "titulo": "PLATAFORMAS",
            "texto": " / ".join(
                platforms[:3]
            ),
        }

    else:

        module_3 = {
            "titulo": "DATO CLAVE",
            "texto": shorten(
                angulo
                or resumen,
                96,
            ),
        }

    return [
        module_1,
        module_2,
        module_3,
    ]



def display_module_title(
    title: str,
) -> str:

    mapping = {
        "QUE CAMBIA": "QU? CAMBIA",
        "TECNOLOGIA": "TECNOLOG?A",
        "INVERSION": "INVERSI?N",
        "POR QUE IMPORTA": "POR QU? IMPORTA",
    }

    title = str(
        title or ""
    ).strip().upper()

    return mapping.get(
        title,
        title,
    )


def build_payload(item: dict) -> dict:

    branch = str(
        item.get(
            "rama",
            "gaming",
        )
    ).strip()

    categoria = str(
        item.get(
            "categoria",
            "NOTICIAS",
        )
    ).strip()

    por_que_importa = str(
        item.get(
            "por_que_importa",
            "",
        )
    ).strip()

    angulo_short = str(
        item.get(
            "anguloShort",
            "",
        )
    ).strip()

    fuente = str(
        item.get(
            "fuente",
            "",
        )
    ).strip()

    fecha_original = str(
        item.get(
            "fecha_original",
            "",
        )
    ).strip()

    modules = build_modules(
        item
    )

    return {
        "numero": item.get(
            "numero",
            "01",
        ),

        "categoria": categoria,

        "rama": branch,

        "fecha": item.get(
            "fecha",
            "",
        ),

        "titulo": item.get(
            "titulo",
            "",
        ),

        "tituloDestacado": item.get(
            "tituloDestacado",
            [],
        ),

        "subheadline": (
            por_que_importa
            or angulo_short
        ),

        "resumen": item.get(
            "resumen",
            "",
        ),

        "resumenDestacado": item.get(
            "resumenDestacado",
            [],
        ),

        "imagen": file_uri(
            item.get(
                "imagen",
                "",
            )
        ),

        "imagenFuente": (
            item.get(
                "imagenFuente",
                "",
            )
            or fuente
        ),

        "module1Title":
            display_module_title(modules[0]["titulo"]),

        "module1Text":
            modules[0]["texto"],

        "module2Title":
            display_module_title(modules[1]["titulo"]),

        "module2Text":
            modules[1]["texto"],

        "module3Title":
            display_module_title(modules[2]["titulo"]),

        "module3Text":
            modules[2]["texto"],

        "fuente": fuente,

        "fechaOriginal":
            fecha_original,

        "avatar": (
            AVATAR_FILE
            .resolve()
            .as_uri()
            if AVATAR_FILE.exists()
            else ""
        ),
    }


# =========================================================
# JAVASCRIPT
# =========================================================

RENDER_SCRIPT = r"""
(payload) => {

    function escapeRegExp(text) {
        return text.replace(
            /[.*+?^${}()|[\]\\]/g,
            '\\$&'
        );
    }


    function applyHighlights(
        text,
        words
    ) {
        let result = text || '';

        for (
            const word
            of (words || [])
        ) {
            if (!word) {
                continue;
            }

            const regex =
                new RegExp(
                    escapeRegExp(word),
                    'gi'
                );

            result =
                result.replace(
                    regex,
                    '<span class="highlight">$&</span>'
                );
        }

        return result;
    }


    function setText(
        id,
        value
    ) {
        const element =
            document.getElementById(id);

        if (element) {
            element.textContent =
                value || '';
        }
    }


    // =====================================================
    // DATOS PRINCIPALES
    // =====================================================

    setText(
        'number',
        payload.numero || '01'
    );

    setText(
        'category',
        payload.categoria || 'NOTICIAS'
    );

    setText(
        'news-date',
        payload.fecha || ''
    );


    // =====================================================
    // TITULAR
    // =====================================================

    const headline =
        document.getElementById(
            'headline'
        );

    headline.innerHTML =
        applyHighlights(
            payload.titulo,
            payload.tituloDestacado
        );


    // =====================================================
    // BAJADA
    // =====================================================

    setText(
        'subheadline',
        payload.subheadline || ''
    );


    // =====================================================
    // RESUMEN
    // =====================================================

    const summary =
        document.getElementById(
            'summary'
        );

    summary.innerHTML =
        applyHighlights(
            payload.resumen,
            payload.resumenDestacado
        );


    // =====================================================
    // MÓDULOS
    // =====================================================

    setText(
        'module-1-title',
        payload.module1Title
    );

    setText(
        'module-1-text',
        payload.module1Text
    );

    setText(
        'module-2-title',
        payload.module2Title
    );

    setText(
        'module-2-text',
        payload.module2Text
    );

    setText(
        'module-3-title',
        payload.module3Title
    );

    setText(
        'module-3-text',
        payload.module3Text
    );


    // =====================================================
    // IMAGEN
    // =====================================================

    const mainImage =
        document.getElementById(
            'main-image'
        );

    const placeholder =
        document.getElementById(
            'image-placeholder'
        );

    if (payload.imagen) {

        mainImage.src =
            payload.imagen;

        mainImage.style.display =
            'block';

        placeholder.style.display =
            'none';

    } else {

        mainImage.removeAttribute(
            'src'
        );

        mainImage.style.display =
            'none';

        placeholder.style.display =
            'flex';
    }


    // =====================================================
    // FUENTE DE IMAGEN
    // =====================================================

    const imageSource =
        document.getElementById(
            'image-source'
        );

    if (
        imageSource
        && payload.imagenFuente
    ) {

        imageSource.innerHTML =
            '<strong>FUENTE:</strong> '
            + payload.imagenFuente;

        imageSource.style.display =
            'block';

    } else if (imageSource) {

        imageSource.innerHTML =
            '';

        imageSource.style.display =
            'none';
    }


    // =====================================================
    // AVATAR
    // =====================================================

    const avatarImage =
        document.getElementById(
            'avatar-image'
        );

    const avatarFallback =
        document.getElementById(
            'avatar-fallback'
        );

    if (
        avatarImage
        && avatarFallback
    ) {

        if (payload.avatar) {

            avatarImage.src =
                payload.avatar;

            avatarImage.style.display =
                'block';

            avatarFallback.style.display =
                'none';

        } else {

            avatarImage.removeAttribute(
                'src'
            );

            avatarImage.style.display =
                'none';

            avatarFallback.style.display =
                'flex';
        }
    }


    // =====================================================
    // RAMA
    // =====================================================

    const card =
        document.getElementById(
            'card'
        );

    card.classList.remove(
        'branch-gaming',
        'branch-tecnologia',
        'branch-cultura_pop'
    );

    card.classList.add(
        'branch-' + (
            payload.rama || 'gaming'
        )
    );


    // =====================================================
    // LONGITUD DEL TITULAR
    // =====================================================

    const headlineLength =
        (
            headline.textContent || ''
        ).trim().length;

    card.classList.remove(
        'title-short',
        'title-medium',
        'title-long',
        'title-xlong'
    );

    if (
        headlineLength <= 34
    ) {

        card.classList.add(
            'title-short'
        );

    } else if (
        headlineLength <= 52
    ) {

        card.classList.add(
            'title-medium'
        );

    } else if (
        headlineLength <= 70
    ) {

        card.classList.add(
            'title-long'
        );

    } else {

        card.classList.add(
            'title-xlong'
        );
    }


    // =====================================================
    // LONGITUD DEL RESUMEN
    // =====================================================

    const summaryLength =
        (
            summary.textContent || ''
        ).trim().length;

    card.classList.remove(
        'summary-short',
        'summary-long'
    );

    if (
        summaryLength <= 145
    ) {

        card.classList.add(
            'summary-short'
        );

    } else if (
        summaryLength >= 235
    ) {

        card.classList.add(
            'summary-long'
        );
    }


    // =====================================================
    // MÓDULOS LARGOS
    // =====================================================

    const moduleText =
        (
            payload.module1Text
            + payload.module2Text
            + payload.module3Text
        );

    if (
        moduleText.length >= 300
    ) {

        card.classList.add(
            'modules-compact'
        );
    }

}
"""


# =========================================================
# CARGAR UNA NOTICIA REAL
# =========================================================

items = json.loads(
    DATA_FILE.read_text(
        encoding="utf-8"
    )
)

if (
    not isinstance(items, list)
    or not items
):
    raise ValueError(
        "data/noticias.json no contiene noticias."
    )


# Usamos la primera noticia.
item = items[0]

payload = build_payload(
    item
)


# =========================================================
# GENERAR PREVIEW
# =========================================================

OUTPUT_FILE.parent.mkdir(
    exist_ok=True
)

with sync_playwright() as p:

    browser = p.chromium.launch()

    page = browser.new_page(
        viewport={
            "width": 1080,
            "height": 1350,
        },
        device_scale_factor=1,
    )

    page.goto(
        TEMPLATE_FILE.resolve().as_uri()
    )

    page.evaluate(
        RENDER_SCRIPT,
        payload,
    )

    page.wait_for_timeout(
        1200
    )

    page.locator(
        "#card"
    ).screenshot(
        path=str(
            OUTPUT_FILE
        )
    )

    browser.close()


print()
print("=" * 60)
print(" TEMPLATE V2 - PREVIEW")
print("=" * 60)
print()
print(
    "Noticia:"
)
print(
    payload["titulo"]
)
print()
print(
    "Imagen generada:"
)
print(
    OUTPUT_FILE
)
print()
