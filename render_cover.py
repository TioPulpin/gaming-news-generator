from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json

from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).resolve().parent

NEWS_FILE = (
    BASE_DIR
    / "data"
    / "noticias.json"
)

AVATAR_FILE = (
    BASE_DIR
    / "assets"
    / "avatar.png"
)

OUTPUT_DIR = (
    BASE_DIR
    / "output"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "00_cover.png"
)

TEMP_HTML = (
    OUTPUT_DIR
    / "_cover.html"
)

LIMA = ZoneInfo(
    "America/Lima"
)

EXPECTED_NEWS = 6


def file_uri(value):
    value = str(
        value or ""
    ).strip()

    if not value:
        return ""

    if (
        value.startswith("http://")
        or value.startswith("https://")
        or value.startswith("file://")
    ):
        return value

    path = Path(value)

    if not path.is_absolute():
        path = (
            BASE_DIR
            / path
        )

    if not path.exists():
        raise FileNotFoundError(
            f"No existe imagen: {path}"
        )

    return (
        path
        .resolve()
        .as_uri()
    )


def load_news():
    if not NEWS_FILE.exists():
        raise FileNotFoundError(
            f"No existe {NEWS_FILE}"
        )

    news = json.loads(
        NEWS_FILE.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        news,
        list,
    ):
        raise RuntimeError(
            "noticias.json no contiene una lista."
        )

    if len(news) != EXPECTED_NEWS:
        raise RuntimeError(
            f"Se esperaban {EXPECTED_NEWS} noticias "
            f"y existen {len(news)}."
        )

    return news


def cover_date(news):
    value = str(
        news[0].get(
            "fecha",
            "",
        )
    ).strip()

    if value:
        return value.upper()

    now = datetime.now(
        LIMA
    )

    months = {
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

    return (
        f"{now.day:02d} "
        f"{months[now.month]} "
        f"{now.year}"
    )


def build_payload(news):
    images = []

    for index, item in enumerate(
        news,
        start=1,
    ):
        image = file_uri(
            item.get(
                "imagen",
                "",
            )
        )

        if not image:
            raise RuntimeError(
                f"La noticia {index:02d} "
                "no tiene imagen."
            )

        images.append({
            "numero":
                f"{index:02d}",
            "imagen":
                image,
        })

    avatar = ""

    if AVATAR_FILE.exists():
        avatar = (
            AVATAR_FILE
            .resolve()
            .as_uri()
        )

    return {
        "fecha":
            cover_date(news),

        "imagenes":
            images,

        "avatar":
            avatar,

        "instagram":
            "@nicolas.herg",

        "tiktok":
            "@tiopulpin",

        "x":
            "@TioPulpin",
    }


HTML = r'''
<!doctype html>

<html lang="es">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=1080, initial-scale=1.0"
>

<title>
    GNG - Portada
</title>

<style>

@font-face {
    font-family: "Anton Local";
    src: url("../assets/fonts/Anton-Regular.ttf") format("truetype");
    font-weight: 400;
    font-style: normal;
}

@font-face {
    font-family: "Oswald Local";
    src: url("../assets/fonts/Oswald-Bold.ttf") format("truetype");
    font-weight: 700;
    font-style: normal;
}

:root {

    --black:
        #050505;

    --black-2:
        #0b0b0d;

    --red:
        #ff2933;

    --red-dark:
        #b90016;

    --white:
        #f7f7f8;

    --gray:
        #bebec4;

    --line:
        rgba(
            255,
            255,
            255,
            0.10
        );

    --red-line:
        rgba(
            255,
            41,
            51,
            0.86
        );

    --font:
        "Oswald Local",
        "DejaVu Sans",
        "Segoe UI",
        Arial,
        sans-serif;

    --condensed:
        "Anton Local",
        "Oswald Local",
        "DejaVu Sans Condensed",
        "Arial Narrow",
        Arial,
        sans-serif;

}


* {

    box-sizing:
        border-box;

}


html,
body {

    margin:
        0;

    padding:
        0;

    width:
        1080px;

    height:
        1350px;

    overflow:
        hidden;

    background:
        #000;

    color:
        var(--white);

    font-family:
        var(--font);

}


.cover {

    position:
        relative;

    width:
        1080px;

    height:
        1350px;

    overflow:
        hidden;

    padding:
        30px
        32px
        25px;

    background:

        radial-gradient(
            circle
            at 90% 8%,
            rgba(
                255,
                20,
                30,
                0.22
            ),
            transparent
            28%
        ),

        radial-gradient(
            circle
            at 5% 90%,
            rgba(
                255,
                20,
                30,
                0.11
            ),
            transparent
            27%
        ),

        linear-gradient(
            180deg,
            #050505,
            #080809
        );

}


.cover::before {

    content:
        "";

    position:
        absolute;

    inset:
        0;

    opacity:
        0.14;

    background-image:

        linear-gradient(
            120deg,
            transparent 0 48%,
            rgba(
                255,
                41,
                51,
                0.25
            ) 48.2%,
            transparent 48.4%
        );

    pointer-events:
        none;

}


.header {

    position:
        relative;

    z-index:
        5;

    height:
        300px;

}


.top-row {

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    height:
        48px;

}


.top-left {

    display:
        flex;

    align-items:
        stretch;

    gap:
        34px;

}


.badge {

    position:
        relative;

    display:
        flex;

    align-items:
        center;

    gap:
        15px;

    min-width:
        320px;

    height:
        48px;

    padding:
        0
        24px;

    background:
        var(--red);

    font-size:
        19px;

    font-weight:
        700;

    letter-spacing:
        3px;

    text-transform:
        uppercase;

}


.badge::after {

    content:
        "";

    position:
        absolute;

    right:
        -22px;

    top:
        0;

    width:
        0;

    height:
        0;

    border-top:
        24px
        solid
        transparent;

    border-bottom:
        24px
        solid
        transparent;

    border-left:
        22px
        solid
        var(--red);

}


.badge-dot {

    width:
        10px;

    height:
        10px;

    background:
        white;

    transform:
        rotate(45deg);

}


.date {

    display:
        flex;

    align-items:
        center;

    padding-left:
        12px;

    color:
        #dddddf;

    font-size:
        20px;

    font-weight:
        900;

    letter-spacing:
        3px;

}


.tagline {

    width:
        190px;

    text-align:
        right;

    color:
        #cfcfd3;

    font-size:
        12px;

    line-height:
        0.88;

    font-weight:
        700;

    letter-spacing:
        4px;

    text-transform:
        uppercase;

}


.tagline strong {

    color:
        var(--red);

    font-size:
        29px;

    margin-left:
        10px;

}


.title-row {

    display:
        grid;

    grid-template-columns:
        190px
        1fr
        165px;

    align-items:
        center;

    gap:
        18px;

    height:
        206px;

    margin-top:
        12px;

}


.big-six {

    font-family:
        "Oswald Local",
        "DejaVu Sans Condensed",
        Arial,
        sans-serif;

    font-size:
        194px;

    line-height:
        0.84;

    font-weight:
        900;

    letter-spacing:
        -10px;

    color:
        var(--red);

    text-shadow:
        0
        8px
        25px
        rgba(
            255,
            0,
            30,
            0.18
        );


    transform:
        scaleX(1.16);

    transform-origin:
        left center;

}


.title-main {

    font-family:
        "Oswald Local",
        "DejaVu Sans Condensed",
        Arial,
        sans-serif;

    font-size:
        90px;

    line-height:
        0.96;

    font-weight:
        700;

    letter-spacing:
        -2px;

    text-transform:
        uppercase;

}


.title-main .red {

    display:
        block;

    margin-top:
        8px;

    color:
        var(--red);

}


.categories {

    padding-left:
        26px;

    border-left:
        2px
        solid
        var(--red);

    color:
        #babac0;

    font-size:
        13px;

    line-height:
        1.72;

    letter-spacing:
        2.5px;

    text-transform:
        uppercase;

}


.topic-line {

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    gap:
        22px;

    height:
        34px;

    margin-top:
        -2px;

    color:
        #f4f4f4;

    font-size:
        20px;

    font-weight:
        900;

    letter-spacing:
        7px;

    text-transform:
        uppercase;

}


.topic-line::before,
.topic-line::after {

    content:
        "";

    height:
        2px;

    flex:
        1;

    background:
        var(--red);

}


.collage {

    position:
        relative;

    z-index:
        5;

    display:
        grid;

    grid-template-columns:
        repeat(
            3,
            1fr
        );

    grid-template-rows:
        repeat(
            2,
            1fr
        );

    gap:
        12px;

    height:
        730px;

    margin-top:
        8px;

}


.tile {

    position:
        relative;

    overflow:
        hidden;

    background:
        #111;

    border:
        2px
        solid
        var(--red);

    clip-path:
        polygon(
            0 0,
            calc(100% - 18px) 0,
            100% 18px,
            100% 100%,
            18px 100%,
            0 calc(100% - 18px)
        );

}


.tile::after {

    content:
        "";

    position:
        absolute;

    inset:
        0;

    pointer-events:
        none;

    background:

        linear-gradient(
            180deg,
            rgba(
                0,
                0,
                0,
                0.02
            ),
            rgba(
                0,
                0,
                0,
                0.08
            )
        );

    box-shadow:
        inset
        0
        0
        24px
        rgba(
            0,
            0,
            0,
            0.28
        );

}


.tile img {

    display:
        block;

    width:
        100%;

    height:
        100%;

    object-fit:
        cover;

}


.number {

    position:
        absolute;

    z-index:
        6;

    left:
        8px;

    top:
        8px;

    min-width:
        62px;

    height:
        49px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    background:
        var(--red);

    color:
        white;

    font-family:
        var(--condensed);

    font-size:
        25px;

    font-weight:
        900;

    box-shadow:
        5px
        5px
        0
        rgba(
            0,
            0,
            0,
            0.35
        );

}


.footer {

    position:
        relative;

    z-index:
        5;

    height:
        240px;

    margin-top:
        16px;

    padding-top:
        20px;

    border-top:
        2px
        solid
        var(--red);

}


.footer-top {

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    gap:
        24px;

}


.brand {

    display:
        flex;

    align-items:
        center;

    gap:
        16px;

    flex:
        1;

}


.avatar {

    width:
        82px;

    height:
        82px;

    border-radius:
        50%;

    overflow:
        hidden;

    flex:
        0
        0
        auto;

    background:
        #111;

    border:
        3px
        solid
        var(--red);

    box-shadow:
        0
        0
        0
        4px
        rgba(
            255,
            41,
            51,
            0.15
        );

}


.avatar img {

    width:
        100%;

    height:
        100%;

    object-fit:
        cover;

}


.brand-copy {

    min-width:
        0;

}


.brand-kicker {

    margin-bottom:
        7px;

    color:
        #a9a9ae;

    font-size:
        10px;

    font-weight:
        800;

    letter-spacing:
        3px;

    text-transform:
        uppercase;

}


.brand-name {

    color:
        white;

    font-family:
        "Oswald Local",
        "DejaVu Sans Condensed",
        Arial,
        sans-serif;

    font-size:
        40px;

    line-height:
        1;

    font-weight:
        700;

    white-space:
        nowrap;

}


.brand-slashes {

    margin-left:
        12px;

    color:
        var(--red);

}


.cta {

    position:
        relative;

    min-width:
        365px;

    height:
        72px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    padding:
        0
        30px;

    background:
        linear-gradient(
            90deg,
            #f0222d,
            #d30e20
        );

    color:
        white;

    font-size:
        23px;

    font-weight:
        900;

    letter-spacing:
        1px;

    text-transform:
        uppercase;

    clip-path:
        polygon(
            0 0,
            calc(100% - 20px) 0,
            100% 20px,
            100% 100%,
            20px 100%,
            0 calc(100% - 20px)
        );

    box-shadow:
        0
        10px
        35px
        rgba(
            255,
            20,
            40,
            0.15
        );

}


.social-row {

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    margin-top:
        20px;

    padding-top:
        16px;

    border-top:
        1px
        solid
        var(--line);

}


.social {

    display:
        flex;

    align-items:
        center;

    gap:
        11px;

    color:
        #f0f0f2;

    font-size:
        18px;

    font-weight:
        800;

}


.social-icon {

    width:
        39px;

    height:
        39px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border:
        2px
        solid
        var(--red);

    color:
        var(--red);

}


.social-icon svg {

    display:
        block;

    width:
        24px;

    height:
        24px;

}


.social-separator {

    width:
        1px;

    height:
        35px;

    background:
        rgba(
            255,
            41,
            51,
            0.45
        );

}


.footer-note {

    color:
        #a8a8ad;

    font-size:
        10px;

    font-weight:
        700;

    letter-spacing:
        3px;

    line-height:
        1.55;

    text-align:
        right;

    text-transform:
        uppercase;

}



/* =========================================================
   PATCH - HERO TITLE STYLE
   ========================================================= */

.hero-main {
    display: grid;
    grid-template-columns: 170px 1fr 190px;
    column-gap: 26px;
    align-items: start;
    margin-top: 10px;
    margin-bottom: 10px;
}

.hero-number {
    display: flex;
    align-items: flex-start;
    justify-content: flex-start;
}

.hero-number .big-number,
.hero-number .count,
.hero-number h1,
.hero-number h2 {
    font-family: "Anton Local", Arial, sans-serif !important;
    font-size: 225px !important;
    line-height: 0.84 !important;
    color: #ff3038 !important;
    letter-spacing: 0 !important;
    transform: none !important;
    text-shadow: none !important;
}

.hero-title {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: flex-start;
    gap: 8px;
    margin-top: 8px;
}

.hero-title .line-1,
.hero-title .title-line-1,
.hero-title .headline-top,
.hero-title .title-top,
.hero-title .hero-top {
    font-family: "Anton Local", Arial, sans-serif !important;
    font-size: 116px !important;
    line-height: 0.92 !important;
    letter-spacing: 0 !important;
    color: #f2f2f2 !important;
    margin: 0 !important;
    padding: 0 !important;
    text-transform: uppercase !important;
}

.hero-title .line-2,
.hero-title .title-line-2,
.hero-title .headline-bottom,
.hero-title .title-bottom,
.hero-title .hero-bottom {
    font-family: "Anton Local", Arial, sans-serif !important;
    font-size: 102px !important;
    line-height: 0.92 !important;
    letter-spacing: 0 !important;
    color: #ff3038 !important;
    margin: 0 !important;
    padding: 0 !important;
    text-transform: uppercase !important;
}

.hero-subline,
.hero-kicker,
.hero-strip,
.hero-tags {
    font-family: "Oswald Local", Arial, sans-serif !important;
    letter-spacing: 6px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
}

.hero-side,
.hero-side * {
    font-family: "Oswald Local", Arial, sans-serif !important;
}

.brand-name,
.footer-brand,
.name,
.author-name {
    font-family: "Oswald Local", Arial, sans-serif !important;
    font-weight: 700 !important;
}

.socials,
.socials * {
    font-family: "Oswald Local", Arial, sans-serif !important;
}


/* =========================================================
   AJUSTE FINAL - TITULO PRINCIPAL
   ========================================================= */

.title-row {
    grid-template-columns:
        170px
        1fr
        165px !important;

    gap:
        6px !important;
}

.title-main {
    font-family:
        "Oswald Local",
        "DejaVu Sans Condensed",
        Arial,
        sans-serif !important;

    font-size:
        92px !important;

    font-weight:
        900 !important;

    letter-spacing:
        -1px !important;

    transform:
        scaleX(1.07);

    transform-origin:
        left center;
}

/* =========================================================
   AJUSTE FINO - CENTRADO FINAL
   ========================================================= */

.title-row,
.hero-title-row {
    grid-template-columns:
        150px
        1fr
        165px !important;

    gap:
        0px !important;

    align-items:
        center !important;

    margin-top:
        10px !important;
}

.title-main,
.hero-title,
.main-title {
    font-size:
        96px !important;

    font-weight:
        900 !important;

    line-height:
        0.92 !important;

    letter-spacing:
        -1.5px !important;

    transform:
        scaleX(1.08) translateX(-10px) !important;

    transform-origin:
        left center !important;
}

/* Baja ligeramente el bloque superior
   para que quede m?s centrado verticalmente */
.cover-main,
.cover-content,
.main-wrap,
.page-inner,
.content-wrap {
    transform:
        translateY(14px) !important;
}

</style>

</head>


<body>

<div class="cover">

    <header class="header">

        <div class="top-row">

            <div class="top-left">

                <div class="badge">

                    <span class="badge-dot"></span>

                    RESUMEN DIARIO

                </div>

                <div
                    class="date"
                    id="date"
                ></div>

            </div>

            <div class="tagline">

                TU DOSIS DIARIA<br>
                DE NOTICIAS<br>
                GAMING Y MÁS

                <strong>
                    ///
                </strong>

            </div>

        </div>


        <div class="title-row">

            <div class="big-six">
                6
            </div>

            <div class="title-main">

                NOTICIAS

                <span class="red">
                    DEL DÍA
                </span>

            </div>

            <div class="categories">

                JUEGOS<br>
                TECH<br>
                ANIME<br>
                INDUSTRIA<br>
                CIBERSEGURIDAD<br>
                Y MÁS

            </div>

        </div>


        <div class="topic-line">

            GAMING · TECNOLOGÍA · CULTURA POP

        </div>

    </header>


    <main
        class="collage"
        id="collage"
    ></main>


    <footer class="footer">

        <div class="footer-top">

            <div class="brand">

                <div class="avatar">

                    <img
                        id="avatar"
                        alt="Nicolas Hernandez"
                    >

                </div>

                <div class="brand-copy">

                    <div class="brand-kicker">

                        NOTICIAS / GAMING / TECH / CULTURA POP

                    </div>

                    <div class="brand-name">

                        NICOLAS HERNANDEZ

                        <span class="brand-slashes">
                            ///
                        </span>

                    </div>

                </div>

            </div>


            <div class="cta">

                DESLIZA PARA VERLAS →

            </div>

        </div>


        <div class="social-row">

            <div class="social">

                <span class="social-icon">

                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                    >

                        <rect
                            x="3"
                            y="3"
                            width="18"
                            height="18"
                            rx="5"
                        />

                        <circle
                            cx="12"
                            cy="12"
                            r="4"
                        />

                        <circle
                            cx="17.5"
                            cy="6.5"
                            r="1"
                            fill="currentColor"
                            stroke="none"
                        />

                    </svg>

                </span>

                <span id="instagram"></span>

            </div>


            <div class="social-separator"></div>


            <div class="social">

                <span class="social-icon">

                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.2"
                        stroke-linecap="round"
                    >

                        <path
                            d="M14 4v10.2a4.2 4.2 0 1 1-3.4-4.1"
                        />

                        <path
                            d="M14 4c1.2 2.7 3.1 4.2 6 4.6"
                        />

                    </svg>

                </span>

                <span id="tiktok"></span>

            </div>


            <div class="social-separator"></div>


            <div class="social">

                <span class="social-icon">

                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.2"
                    >

                        <path
                            d="M5 4l14 16"
                        />

                        <path
                            d="M19 4L5 20"
                        />

                    </svg>

                </span>

                <span id="x"></span>

            </div>


            <div class="footer-note">

                MISMAS NOTICIAS.<br>
                MÁS PASIÓN.

            </div>

        </div>

    </footer>

</div>


<script>

const payload =
    __PAYLOAD__;


document
    .getElementById(
        "date"
    )
    .textContent =
        payload.fecha;


document
    .getElementById(
        "instagram"
    )
    .textContent =
        payload.instagram;


document
    .getElementById(
        "tiktok"
    )
    .textContent =
        payload.tiktok;


document
    .getElementById(
        "x"
    )
    .textContent =
        payload.x;


const avatar =
    document
    .getElementById(
        "avatar"
    );


if (
    payload.avatar
) {

    avatar.src =
        payload.avatar;

}


const collage =
    document
    .getElementById(
        "collage"
    );


for (
    const item
    of payload.imagenes
) {

    const tile =
        document
        .createElement(
            "div"
        );

    tile.className =
        "tile";


    const image =
        document
        .createElement(
            "img"
        );

    image.src =
        item.imagen;

    image.alt =
        "Noticia "
        + item.numero;


    const number =
        document
        .createElement(
            "div"
        );

    number.className =
        "number";

    number.textContent =
        item.numero;


    tile.appendChild(
        image
    );

    tile.appendChild(
        number
    );

    collage.appendChild(
        tile
    );

}

</script>

</body>

</html>
'''


def main():
    news = load_news()

    payload = build_payload(
        news
    )

    html = HTML.replace(
        "__PAYLOAD__",
        json.dumps(
            payload,
            ensure_ascii=False,
        ),
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    TEMP_HTML.write_text(
        html,
        encoding="utf-8",
    )

    print()
    print("=" * 68)
    print(" GENERANDO PORTADA GNG")
    print("=" * 68)
    print()

    with sync_playwright() as p:
        browser = (
            p.chromium.launch()
        )

        page = browser.new_page(
            viewport={
                "width": 1080,
                "height": 1350,
            },
            device_scale_factor=1,
        )

        page.goto(
            TEMP_HTML
            .resolve()
            .as_uri(),
            wait_until="load",
        )

        page.wait_for_function(
            """
            () => Array.from(
                document.images
            ).every(
                img =>
                    img.complete
                    && img.naturalWidth > 0
            )
            """
        )

        page.wait_for_timeout(
            300
        )

        page.evaluate(
            "() => document.fonts.ready.then(() => true)"
        )

        image_bytes = page.locator(
            ".cover"
        ).screenshot()

        OUTPUT_FILE.write_bytes(
            image_bytes
        )

        browser.close()

    print(
        "OK - Portada generada:"
    )

    print(
        OUTPUT_FILE
    )

    print()


if __name__ == "__main__":
    main()
