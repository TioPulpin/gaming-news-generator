import json
import re
import unicodedata
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



def normalize_visual_module_text(
    text: str,
) -> str:

    text = str(
        text or ""
    ).strip()

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = text.encode(
        "ascii",
        "ignore",
    ).decode(
        "ascii"
    )

    text = re.sub(
        r"[^a-zA-Z0-9]+",
        " ",
        text.lower(),
    )

    return " ".join(
        text.split()
    )


def visual_module_is_weak(
    module: dict,
) -> bool:

    title = normalize_visual_module_text(
        module.get(
            "titulo",
            "",
        )
    ).upper()

    value = str(
        module.get(
            "texto",
            "",
        )
    ).strip()

    clean = normalize_visual_module_text(
        value
    )

    words = clean.split()

    length = len(
        value
    )


    # POR QUE IMPORTA es el modulo
    # editorial principal.
    if title == "POR QUE IMPORTA":
        return False


    # Fechas demasiado simples:
    # 2027
    # marzo de 2027
    if title in {
        "FECHA",
        "LANZAMIENTO",
    }:
        return length < 18


    # Una unica plataforma no merece
    # necesariamente una columna completa.
    if title == "PLATAFORMAS":
        return (
            len(words) <= 1
            and length <= 15
        )


    # Una plataforma concreta como
    # Nintendo Switch 2 si tiene entidad.
    if title == "PLATAFORMA":
        return length < 14


    # Nombres tecnologicos pueden ser breves
    # pero relevantes: NVLink Fusion.
    if title == "TECNOLOGIA":
        return length < 10


    # Cifras de inversion/precio se conservan
    # si son algo mas que un numero aislado.
    if title in {
        "INVERSION",
        "PRECIO",
    }:
        return (
            length < 10
            or len(words) < 2
        )


    # Regla general.
    if length <= 9:
        return True

    if (
        len(words) == 1
        and length <= 14
    ):
        return True

    return False


def visual_module_score(
    module: dict,
) -> int:

    title = normalize_visual_module_text(
        module.get(
            "titulo",
            "",
        )
    ).upper()

    text = str(
        module.get(
            "texto",
            "",
        )
    ).strip()

    words = (
        normalize_visual_module_text(
            text
        ).split()
    )

    score = (
        min(
            len(text),
            100,
        )
        +
        len(words) * 4
    )

    bonuses = {
        "POR QUE IMPORTA": 70,
        "DATO CLAVE": 30,
        "IMPACTO": 25,
        "QUE CAMBIA": 20,
        "INVERSION": 25,
        "PRECIO": 25,
        "TECNOLOGIA": 18,
        "PLATAFORMA": 18,
        "FECHA": 15,
    }

    score += bonuses.get(
        title,
        0,
    )

    if visual_module_is_weak(
        module
    ):
        score -= 120

    return score


def modules_are_duplicates(
    first: dict,
    second: dict,
) -> bool:

    a = normalize_visual_module_text(
        first.get(
            "texto",
            "",
        )
    )

    b = normalize_visual_module_text(
        second.get(
            "texto",
            "",
        )
    )

    if not a or not b:
        return False

    if a == b:
        return True

    words_a = set(
        a.split()
    )

    words_b = set(
        b.split()
    )

    if (
        not words_a
        or not words_b
    ):
        return False

    overlap = len(
        words_a & words_b
    )

    smaller = min(
        len(words_a),
        len(words_b),
    )

    similarity = (
        overlap
        / smaller
    )

    return (
        smaller >= 5
        and similarity >= 0.82
    )


def select_visual_modules(
    modules: list[dict],
) -> list[dict]:

    modules = [
        dict(module)
        for module in modules
        if isinstance(
            module,
            dict,
        )
    ]

    if len(modules) <= 2:
        return modules


    # =====================================================
    # 1. ELIMINAR REDUNDANCIA
    # =====================================================

    duplicate_pairs = []

    for i in range(
        len(modules)
    ):
        for j in range(
            i + 1,
            len(modules),
        ):

            if modules_are_duplicates(
                modules[i],
                modules[j],
            ):

                duplicate_pairs.append(
                    (i, j)
                )


    if duplicate_pairs:

        i, j = duplicate_pairs[0]

        score_i = visual_module_score(
            modules[i]
        )

        score_j = visual_module_score(
            modules[j]
        )

        remove_index = (
            i
            if score_i < score_j
            else j
        )

        result = [
            module
            for index, module
            in enumerate(
                modules
            )
            if index != remove_index
        ]

        return result[:2]


    # =====================================================
    # 2. DETECTAR MODULO POBRE
    # =====================================================

    weak_indexes = [
        index
        for index, module
        in enumerate(
            modules
        )
        if visual_module_is_weak(
            module
        )
    ]


    if weak_indexes:

        # Se elimina solamente uno.
        remove_index = min(
            weak_indexes,
            key=lambda index:
                visual_module_score(
                    modules[index]
                ),
        )

        result = [
            module
            for index, module
            in enumerate(
                modules
            )
            if index != remove_index
        ]

        return result[:2]


    # =====================================================
    # 3. LOS TRES APORTAN VALOR
    # =====================================================

    return modules[:3]



def select_two_visual_modules(
    modules: list[dict],
) -> list[dict]:

    modules = [
        dict(module)
        for module in modules
        if isinstance(
            module,
            dict,
        )
    ]

    if not modules:
        return []


    # =====================================================
    # QUITAR MODULOS DEBILES
    # =====================================================

    useful = [
        module
        for module in modules
        if not visual_module_is_weak(
            module
        )
    ]


    # Si el filtro fue demasiado agresivo,
    # conservamos los mejores disponibles.
    if len(useful) < 2:

        useful = sorted(
            modules,
            key=visual_module_score,
            reverse=True,
        )


    # =====================================================
    # QUITAR REDUNDANCIA
    # =====================================================

    clean = []

    for module in useful:

        duplicate = False

        for existing in clean:

            if modules_are_duplicates(
                module,
                existing,
            ):
                duplicate = True
                break

        if not duplicate:
            clean.append(
                module
            )


    if len(clean) < 2:

        clean = useful


    # =====================================================
    # PRIORIZAR:
    # 1 editorial + 1 dato concreto
    # =====================================================

    editorial_titles = {
        "POR QUE IMPORTA",
        "DATO CLAVE",
        "QUE CAMBIA",
        "IMPACTO",
        "CONTEXTO",
        "INDUSTRIA",
        "COMUNIDAD",
    }

    concrete_titles = {
        "FECHA",
        "PRECIO",
        "PLATAFORMA",
        "PLATAFORMAS",
        "LANZAMIENTO",
        "DISPONIBILIDAD",
        "TECNOLOGIA",
        "FRANQUICIA",
        "INVERSION",
    }


    def normalized_title(
        module,
    ):
        return (
            normalize_visual_module_text(
                module.get(
                    "titulo",
                    "",
                )
            )
            .upper()
        )


    editorial = [
        module
        for module in clean
        if normalized_title(
            module
        ) in editorial_titles
    ]

    concrete = [
        module
        for module in clean
        if normalized_title(
            module
        ) in concrete_titles
    ]


    selected = []


    # Mejor modulo editorial.
    if editorial:

        best_editorial = max(
            editorial,
            key=visual_module_score,
        )

        selected.append(
            best_editorial
        )


    # Mejor dato concreto.
    if concrete:

        best_concrete = max(
            concrete,
            key=visual_module_score,
        )

        if (
            best_concrete
            not in selected
        ):
            selected.append(
                best_concrete
            )


    # Completar con el mejor restante.
    ranked = sorted(
        clean,
        key=visual_module_score,
        reverse=True,
    )

    for module in ranked:

        if (
            module
            not in selected
        ):
            selected.append(
                module
            )

        if len(selected) == 2:
            break


    return selected[:2]


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

    modules = select_two_visual_modules(
        modules
    )

    module_count = len(
        modules
    )

    display_modules = list(
        modules
    )

    while len(
        display_modules
    ) < 3:

        display_modules.append({
            "titulo": "",
            "texto": "",
        })

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

        "moduleCount": module_count,

        "module1Title":
            display_module_title(display_modules[0]["titulo"]),

        "module1Text":
            display_modules[0]["texto"],

        "module2Title":
            display_module_title(display_modules[1]["titulo"]),

        "module2Text":
            display_modules[1]["texto"],

        "module3Title":
            display_module_title(display_modules[2]["titulo"]),

        "module3Text":
            display_modules[2]["texto"],

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
    // ESCALA AUTOMATICA DE LOS MODULOS
    // =====================================================

    function scaleModuleText(id) {

        const element =
            document.getElementById(id);

        if (!element) {
            return;
        }

        const length =
            (
                element.textContent || ''
            ).trim().length;

        element.classList.remove(
            'module-xl',
            'module-lg',
            'module-md',
            'module-sm'
        );

        if (length <= 14) {

            element.classList.add(
                'module-xl'
            );

        } else if (length <= 30) {

            element.classList.add(
                'module-lg'
            );

        } else if (length <= 58) {

            element.classList.add(
                'module-md'
            );

        } else {

            element.classList.add(
                'module-sm'
            );
        }
    }


    scaleModuleText(
        'module-1-text'
    );

    scaleModuleText(
        'module-2-text'
    );

    scaleModuleText(
        'module-3-text'
    );




    // =====================================================
    // LAYOUT 2 / 3 MODULOS DEFINIDO POR PYTHON
    // =====================================================

    const moduleContainer =
        document.getElementById(
            'info-modules'
        );

    if (moduleContainer) {

        const wrappers =
            Array.from(
                moduleContainer
                .querySelectorAll(
                    '.info-module'
                )
            );

        const count =
            Number(
                payload.moduleCount
                || 3
            );

        moduleContainer.classList.remove(
            'modules-2',
            'modules-3'
        );

        moduleContainer.classList.add(
            count === 2
                ? 'modules-2'
                : 'modules-3'
        );

        wrappers.forEach(
            (
                wrapper,
                index
            ) => {

                wrapper.style.display =
                    index < count
                        ? ''
                        : 'none';

                wrapper.classList.remove(
                    'module-divider'
                );
            }
        );

        if (
            count === 2
            && wrappers[0]
        ) {

            wrappers[0]
                .classList
                .add(
                    'module-divider'
                );
        }
    }




    // =====================================================
    // LAYOUT FINAL SEGUN MODULOS REALMENTE VISIBLES
    // =====================================================

    const finalModuleContainer =
        document.getElementById(
            'info-modules'
        );

    if (finalModuleContainer) {

        const finalWrappers =
            Array.from(
                finalModuleContainer.querySelectorAll(
                    '.info-module'
                )
            );

        const usefulWrappers = [];

        finalWrappers.forEach(
            (wrapper) => {

                const value =
                    wrapper.querySelector(
                        '.module-text'
                    );

                const title =
                    wrapper.querySelector(
                        '.module-title'
                    );

                const hasValue =
                    value
                    && (
                        value.textContent
                        || ''
                    ).trim();

                const hasTitle =
                    title
                    && (
                        title.textContent
                        || ''
                    ).trim();

                if (
                    hasValue
                    && hasTitle
                ) {

                    wrapper.style.display =
                        'flex';

                    usefulWrappers.push(
                        wrapper
                    );

                } else {

                    wrapper.style.display =
                        'none';
                }

                wrapper.classList.remove(
                    'module-divider'
                );
            }
        );


        // Nunca dejamos una tercera columna vacia.
        const visibleCount =
            Math.max(
                2,
                Math.min(
                    usefulWrappers.length,
                    3
                )
            );


        finalModuleContainer.classList.remove(
            'modules-2',
            'modules-3'
        );


        if (
            usefulWrappers.length === 2
        ) {

            finalModuleContainer.classList.add(
                'modules-2'
            );

            finalModuleContainer.style.gridTemplateColumns =
                'repeat(2, minmax(0, 1fr))';

            usefulWrappers[0]
                .classList
                .add(
                    'module-divider'
                );

        } else {

            finalModuleContainer.classList.add(
                'modules-3'
            );

            finalModuleContainer.style.gridTemplateColumns =
                'repeat(3, minmax(0, 1fr))';
        }
    }





    // =====================================================
    // TEMPLATE V2 FINAL - SIEMPRE DOS MODULOS
    // =====================================================

    const twoModuleContainer =
        document.getElementById(
            'info-modules'
        );

    if (twoModuleContainer) {

        const twoModuleWrappers =
            Array.from(
                twoModuleContainer
                .querySelectorAll(
                    '.info-module'
                )
            );

        twoModuleContainer.classList.remove(
            'modules-3'
        );

        twoModuleContainer.classList.add(
            'modules-2'
        );

        twoModuleContainer.style.gridTemplateColumns =
            'repeat(2, minmax(0, 1fr))';


        twoModuleWrappers.forEach(
            (
                wrapper,
                index
            ) => {

                wrapper.style.display =
                    index < 2
                        ? 'flex'
                        : 'none';

                wrapper.classList.remove(
                    'module-divider'
                );
            }
        );


        if (
            twoModuleWrappers[0]
        ) {

            twoModuleWrappers[0]
                .classList
                .add(
                    'module-divider'
                );
        }
    }



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
# CARGAR TODAS LAS NOTICIAS
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


# =========================================================
# DIRECTORIO DE PREVIEWS V2
# =========================================================

OUTPUT_DIR = (
    BASE_DIR
    / "output"
    / "v2_candidate"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# GENERAR LAS 6 TARJETAS V2
# =========================================================

generated = []

with sync_playwright() as p:

    browser = p.chromium.launch()

    page = browser.new_page(
        viewport={
            "width": 1080,
            "height": 1350,
        },
        device_scale_factor=1,
    )

    for item in items:

        payload = build_payload(
            item
        )

        # Recargamos la plantilla para que
        # ninguna clase de la tarjeta anterior
        # se herede a la siguiente.
        page.goto(
            TEMPLATE_FILE.resolve().as_uri()
        )

        page.evaluate(
            RENDER_SCRIPT,
            payload,
        )

        page.wait_for_timeout(
            800
        )

        numero = str(
            payload.get(
                "numero",
                "00",
            )
        )

        output_file = (
            OUTPUT_DIR
            / f"{numero}_template_v2.png"
        )

        page.locator(
            "#card"
        ).screenshot(
            path=str(
                output_file
            )
        )

        generated.append(
            output_file
        )

        print(
            "Generado:",
            output_file.name,
        )

    browser.close()


# =========================================================
# RESULTADO
# =========================================================

print()
print("=" * 64)
print(" GAMING NEWS GENERATOR - TEMPLATE V2")
print("=" * 64)
print()

for file in generated:
    print(file)

print()
print(
    "Total:",
    len(generated),
    "tarjetas"
)
print()
