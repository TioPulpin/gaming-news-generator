from pathlib import Path
import json

from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "07_cta.png"
TEMP_HTML = OUTPUT_DIR / "_cta.html"

AVATAR_FILE = BASE_DIR / "assets" / "avatar.png"


def file_uri(path: Path):
    if not path.exists():
        return ""

    return path.resolve().as_uri()


payload = {
    "avatar": file_uri(AVATAR_FILE),
    "instagram": "@nicolas.herg",
    "tiktok": "@tiopulpin",
    "x": "@TioPulpin",
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
    GNG CTA
</title>


<style>

@font-face {
    font-family: "Anton Local";
    src: url("../assets/fonts/Anton-Regular.ttf")
         format("truetype");
    font-weight: 400;
    font-style: normal;
}

@font-face {
    font-family: "Oswald Local";
    src: url("../assets/fonts/Oswald-Bold.ttf")
         format("truetype");
    font-weight: 700;
    font-style: normal;
}


:root {

    --black: #050505;

    --red: #ff2933;

    --red-dark: #a90614;

    --white: #f7f7f7;

    --gray: #aaaab0;

    --font-display:
        "Anton Local",
        Arial,
        sans-serif;

    --font-ui:
        "Oswald Local",
        Arial,
        sans-serif;

}


* {
    box-sizing: border-box;
}


html,
body {

    width: 1080px;
    height: 1350px;

    margin: 0;
    padding: 0;

    overflow: hidden;

    background: #000;

    color: var(--white);

    font-family: var(--font-ui);

}


.cta-card {

    position: relative;

    width: 1080px;
    height: 1350px;

    overflow: hidden;

    padding:
        30px
        32px
        24px;

    background:

        radial-gradient(
            circle at 95% 10%,
            rgba(255, 30, 45, 0.24),
            transparent 31%
        ),

        radial-gradient(
            circle at 10% 77%,
            rgba(255, 30, 45, 0.18),
            transparent 34%
        ),

        linear-gradient(
            180deg,
            #050505 0%,
            #080809 100%
        );

}


.cta-card::before {

    content: "";

    position: absolute;

    inset: 0;

    background:
        linear-gradient(
            125deg,
            transparent 0 45%,
            rgba(255, 41, 51, 0.14) 45.15%,
            transparent 45.3%
        );

    pointer-events: none;

}


/* ======================================================
   CABECERA
   ====================================================== */

.top {

    position: relative;

    z-index: 5;

    display: flex;

    align-items: flex-start;

    justify-content: space-between;

}


.badge {

    position: relative;

    display: flex;

    align-items: center;

    gap: 14px;

    height: 49px;

    min-width: 320px;

    padding:
        0
        24px;

    background:
        var(--red);

    font-size: 19px;

    font-weight: 700;

    letter-spacing: 3px;

    text-transform: uppercase;

}


.badge::after {

    content: "";

    position: absolute;

    right: -22px;

    top: 0;

    width: 0;
    height: 0;

    border-top:
        24.5px solid transparent;

    border-bottom:
        24.5px solid transparent;

    border-left:
        22px solid var(--red);

}


.badge-dot {

    width: 10px;
    height: 10px;

    background: white;

    transform: rotate(45deg);

}


.top-right {

    display: flex;

    align-items: flex-start;

    gap: 18px;

    text-align: right;

}


.top-tagline {

    color: #ddd;

    font-size: 12px;

    line-height: 1.45;

    letter-spacing: 4px;

    font-weight: 700;

    text-transform: uppercase;

}


.slashes {

    color: var(--red);

    font-family: var(--font-display);

    font-size: 31px;

    line-height: 1;
}


/* ======================================================
   TITULO
   ====================================================== */

.hero {

    position: relative;

    z-index: 5;

    margin-top: 95px;

    text-align: center;

}


.hero-white,
.hero-red {

    font-family:
        var(--font-display);

    text-transform: uppercase;

    line-height: 0.94;

    letter-spacing: 0;

}


.hero-white {

    color: white;

    font-size: 101px;

}


.hero-red {

    margin-top: 12px;

    color: var(--red);

    font-size: 108px;

}


.comment-line {

    display: flex;

    align-items: center;

    gap: 26px;

    margin-top: 28px;

    color: white;

    font-size: 23px;

    font-weight: 700;

    letter-spacing: 6px;

    text-transform: uppercase;

}


.comment-line::before,
.comment-line::after {

    content: "";

    flex: 1;

    height: 2px;

    background:
        var(--red);

}


/* ======================================================
   ZONA CENTRAL
   ====================================================== */

.middle {

    position: relative;

    z-index: 5;

    display: grid;

    grid-template-columns:
        45%
        55%;

    height: 485px;

    margin-top: 26px;

}


/* CONTROL DECORATIVO */

.controller-area {

    position: relative;

    overflow: hidden;

}


.controller {

    position: absolute;

    left: -95px;

    bottom: -45px;

    width: 555px;

    height: 390px;

    transform:
        rotate(-12deg);

    filter:
        drop-shadow(
            0
            0
            28px
            rgba(255, 20, 35, 0.18)
        );

}


.controller-body {

    position: absolute;

    inset:
        40px
        50px
        40px;

    border-radius:
        170px
        170px
        220px
        220px;

    border:
        4px solid
        rgba(255, 41, 51, 0.75);

    background:

        radial-gradient(
            circle at 60% 40%,
            rgba(255, 41, 51, 0.12),
            transparent 45%
        ),

        linear-gradient(
            160deg,
            #151516,
            #050505
        );

}


.stick {

    position: absolute;

    width: 78px;
    height: 78px;

    border-radius: 50%;

    background:
        #090909;

    border:
        4px solid
        rgba(255, 41, 51, 0.55);

}


.stick::after {

    content: "";

    position: absolute;

    inset: 17px;

    border-radius: 50%;

    background:
        #18181a;

}


.stick-left {

    left: 120px;
    top: 160px;

}


.stick-right {

    left: 290px;
    top: 205px;

}


.dpad {

    position: absolute;

    left: 105px;
    top: 70px;

    width: 105px;
    height: 105px;

}


.dpad::before,
.dpad::after {

    content: "";

    position: absolute;

    background:
        #18181a;

    border:
        2px solid
        rgba(255, 41, 51, 0.42);

}


.dpad::before {

    width: 36px;
    height: 105px;

    left: 34px;

}


.dpad::after {

    width: 105px;
    height: 36px;

    top: 34px;

}


.buttons {

    position: absolute;

    right: 105px;
    top: 82px;

    width: 125px;
    height: 125px;

}


.button {

    position: absolute;

    width: 42px;
    height: 42px;

    border-radius: 50%;

    border:
        3px solid
        rgba(255, 41, 51, 0.75);

    background:
        #101012;

}


.b1 { left: 42px; top: 0; }
.b2 { right: 0; top: 42px; }
.b3 { left: 42px; bottom: 0; }
.b4 { left: 0; top: 42px; }


/* ACCIONES */

.actions {

    display: flex;

    flex-direction: column;

    justify-content: center;

    gap: 18px;

    padding-left: 28px;

}


.action {

    display: grid;

    grid-template-columns:
        88px
        3px
        1fr;

    align-items: center;

    gap: 24px;

}


.action-icon {

    width: 88px;
    height: 82px;

    display: flex;

    align-items: center;

    justify-content: center;

    border:
        3px solid
        var(--red);

    color:
        var(--red);

}


.action-icon svg {

    width: 44px;
    height: 44px;

}


.action-line {

    width: 3px;
    height: 70px;

    background:
        var(--red);

}


.action-title {

    color: white;

    font-size: 39px;

    font-weight: 700;

    line-height: 1;

    text-transform: uppercase;

}


.action-sub {

    margin-top: 5px;

    color: #a9a9af;

    font-size: 18px;

    letter-spacing: 4px;

    text-transform: uppercase;

}


/* ======================================================
   BOTON SIGUEME
   ====================================================== */

.follow {

    position: absolute;

    z-index: 8;

    right: 42px;

    bottom: 242px;

    width: 545px;

    height: 112px;

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 28px;

    color: white;

    background:
        linear-gradient(
            90deg,
            #ff2933,
            #d71023
        );

    clip-path:
        polygon(
            0 0,
            calc(100% - 30px) 0,
            100% 30px,
            100% 100%,
            30px 100%,
            0 calc(100% - 30px)
        );

}


.follow-icon {

    width: 68px;

    height: 68px;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 52px;

    border-right:
        2px solid
        rgba(255,255,255,0.65);

    padding-right:
        26px;

}


.follow-text {

    font-family:
        var(--font-display);

    font-size:
        63px;

    line-height:
        1;

    text-transform:
        uppercase;

}


/* ======================================================
   FOOTER
   ====================================================== */

.footer {

    position: absolute;

    z-index: 5;

    left: 32px;
    right: 32px;
    bottom: 24px;

    height: 205px;

    padding-top: 17px;

    border-top:
        2px solid
        var(--red);

}


.footer-top {

    display: flex;

    align-items: center;

    justify-content: space-between;

}


.brand {

    display: flex;

    align-items: center;

    gap: 15px;

}


.avatar {

    width: 75px;
    height: 75px;

    overflow: hidden;

    border-radius: 50%;

    border:
        3px solid
        var(--red);

}


.avatar img {

    width: 100%;
    height: 100%;

    object-fit: cover;

}


.brand-kicker {

    color:
        #a6a6ab;

    font-size:
        10px;

    letter-spacing:
        3px;

    text-transform:
        uppercase;

}


.brand-name {

    margin-top: 4px;

    color:
        white;

    font-size:
        38px;

    font-weight:
        700;

    line-height:
        1;

}


.brand-name span {

    color:
        var(--red);

    margin-left:
        13px;

}


.footer-message {

    color:
        #c2c2c6;

    font-size:
        12px;

    line-height:
        1.55;

    letter-spacing:
        4px;

    text-align:
        right;

    text-transform:
        uppercase;

}


.social-row {

    display: flex;

    align-items: center;

    justify-content: space-between;

    margin-top: 17px;

    padding-top: 15px;

    border-top:
        1px solid
        rgba(255,255,255,0.10);

}


.social {

    display: flex;

    align-items: center;

    gap: 11px;

    color: white;

    font-size: 18px;

    font-weight: 700;

}


.social-icon {

    width: 39px;
    height: 39px;

    display: flex;

    align-items: center;

    justify-content: center;

    color:
        var(--red);

    border:
        2px solid
        var(--red);

}


.social-icon svg {

    width: 23px;
    height: 23px;

}


.sep {

    width: 1px;
    height: 34px;

    background:
        rgba(255,41,51,0.45);

}



/* =========================================================
   CTA LOWER V2
   ========================================================= */


/* MANDO */

.controller {
    display: none !important;
}

.controller-svg {

    position:
        absolute;

    width:
        570px;

    height:
        auto;

    left:
        -72px;

    bottom:
        -10px;

    transform:
        rotate(-8deg);

    filter:
        drop-shadow(
            0 18px 34px rgba(0,0,0,0.55)
        )
        drop-shadow(
            0 0 20px rgba(255,41,51,0.12)
        );

}


/* M?S ESPACIO PARA LAS ACCIONES */

.middle {

    grid-template-columns:
        47%
        53% !important;

}


.actions {

    gap:
        24px !important;

    padding-left:
        8px !important;

}


.action {

    grid-template-columns:
        100px
        3px
        1fr !important;

    gap:
        21px !important;

}


.action-icon {

    width:
        100px !important;

    height:
        90px !important;

    border-width:
        3px !important;

}


.action-icon svg {

    width:
        50px !important;

    height:
        50px !important;

}


.action-line {

    height:
        76px !important;

}


.action-title {

    font-size:
        45px !important;

    line-height:
        0.95 !important;

    letter-spacing:
        0.5px !important;

}


.action-sub {

    margin-top:
        7px !important;

    font-size:
        20px !important;

    letter-spacing:
        3.5px !important;

}


/* SIGUEME */

.follow {

    width:
        565px !important;

    height:
        118px !important;

    gap:
        28px !important;

}


.follow-icon {

    width:
        82px !important;

    height:
        72px !important;

    padding-right:
        28px !important;

    color:
        white;

}


.follow-icon svg {

    width:
        56px;

    height:
        56px;

}


.follow-text {

    font-family:
        "Oswald Local",
        Arial,
        sans-serif !important;

    font-size:
        72px !important;

    font-weight:
        700 !important;

    letter-spacing:
        4px !important;

    transform:
        scaleX(1.08);

    transform-origin:
        center;

}


/* REDES M?S GRANDES Y M?S JUNTAS */

.social-row {

    justify-content:
        center !important;

    gap:
        27px !important;

}


.social {

    gap:
        12px !important;

    font-size:
        21px !important;

}


.social-icon {

    width:
        45px !important;

    height:
        45px !important;

}


.social-icon svg {

    width:
        27px !important;

    height:
        27px !important;

}


.sep {

    height:
        37px !important;

    margin:
        0 4px !important;

}


</style>

</head>


<body>


<div class="cta-card">


    <div class="top">

        <div class="badge">

            <span class="badge-dot"></span>

            FINAL DEL CARRUSEL

        </div>


        <div class="top-right">

            <div class="top-tagline">

                TU DOSIS DIARIA<br>
                DE NOTICIAS<br>
                GAMING Y MÁS

            </div>

            <div class="slashes">
                ///
            </div>

        </div>

    </div>


    <section class="hero">

        <div class="hero-white">

            ¿CUÁL FUE TU

        </div>

        <div class="hero-red">

            NOTICIA FAVORITA?

        </div>


        <div class="comment-line">

            CUÉNTAME EN LOS COMENTARIOS

        </div>

    </section>


    <section class="middle">


        <div class="controller-area">

            <svg
                class="controller-svg"
                viewBox="0 0 560 420"
                xmlns="http://www.w3.org/2000/svg"
                aria-label="Mando de videojuegos"
            >

                <defs>

                    <linearGradient
                        id="padBody"
                        x1="0"
                        y1="0"
                        x2="1"
                        y2="1"
                    >

                        <stop
                            offset="0%"
                            stop-color="#1a1a1d"
                        />

                        <stop
                            offset="55%"
                            stop-color="#09090b"
                        />

                        <stop
                            offset="100%"
                            stop-color="#030304"
                        />

                    </linearGradient>

                    <radialGradient
                        id="padGlow"
                        cx="50%"
                        cy="45%"
                        r="65%"
                    >

                        <stop
                            offset="0%"
                            stop-color="#ff2933"
                            stop-opacity="0.18"
                        />

                        <stop
                            offset="100%"
                            stop-color="#ff2933"
                            stop-opacity="0"
                        />

                    </radialGradient>

                </defs>


                <path
                    d="
                    M150 82
                    C108 86 78 111 62 154
                    L26 278
                    C14 321 38 355 75 349
                    C91 346 108 337 126 325
                    L173 292
                    C194 278 218 270 244 270
                    H316
                    C342 270 366 278 387 292
                    L434 325
                    C452 337 469 346 485 349
                    C522 355 546 321 534 278
                    L498 154
                    C482 111 452 86 410 82
                    C369 78 338 96 313 122
                    H247
                    C222 96 191 78 150 82
                    Z"
                    fill="url(#padBody)"
                    stroke="#ff2933"
                    stroke-width="4"
                />

                <path
                    d="
                    M150 82
                    C108 86 78 111 62 154
                    L26 278
                    C14 321 38 355 75 349
                    C91 346 108 337 126 325
                    L173 292
                    C194 278 218 270 244 270
                    H316
                    C342 270 366 278 387 292
                    L434 325
                    C452 337 469 346 485 349
                    C522 355 546 321 534 278
                    L498 154
                    C482 111 452 86 410 82
                    C369 78 338 96 313 122
                    H247
                    C222 96 191 78 150 82
                    Z"
                    fill="url(#padGlow)"
                />


                <!-- D-PAD -->

                <g
                    fill="#111216"
                    stroke="#ff2933"
                    stroke-width="2.5"
                >

                    <rect
                        x="113"
                        y="128"
                        width="38"
                        height="112"
                        rx="5"
                    />

                    <rect
                        x="76"
                        y="165"
                        width="112"
                        height="38"
                        rx="5"
                    />

                </g>


                <!-- STICKS -->

                <g>

                    <circle
                        cx="205"
                        cy="259"
                        r="43"
                        fill="#070708"
                        stroke="#ff2933"
                        stroke-width="4"
                    />

                    <circle
                        cx="205"
                        cy="259"
                        r="28"
                        fill="#17181b"
                    />

                    <circle
                        cx="355"
                        cy="259"
                        r="43"
                        fill="#070708"
                        stroke="#ff2933"
                        stroke-width="4"
                    />

                    <circle
                        cx="355"
                        cy="259"
                        r="28"
                        fill="#17181b"
                    />

                </g>


                <!-- BOTONES -->

                <g
                    fill="#0d0e11"
                    stroke="#ff2933"
                    stroke-width="3"
                >

                    <circle cx="430" cy="131" r="25"/>
                    <circle cx="469" cy="169" r="25"/>
                    <circle cx="430" cy="207" r="25"/>
                    <circle cx="391" cy="169" r="25"/>

                </g>


                <!-- SIMBOLOS -->

                <g
                    fill="none"
                    stroke="#ff2933"
                    stroke-width="3"
                >

                    <path
                        d="M430 117l12 20h-24z"
                    />

                    <circle
                        cx="469"
                        cy="169"
                        r="11"
                    />

                    <rect
                        x="419"
                        y="196"
                        width="22"
                        height="22"
                    />

                    <path
                        d="
                        M382 160
                        l18 18
                        M400 160
                        l-18 18
                        "
                    />

                </g>


                <!-- CENTRO -->

                <rect
                    x="247"
                    y="135"
                    width="66"
                    height="35"
                    rx="8"
                    fill="#111216"
                    stroke="#ff2933"
                    stroke-width="2"
                />

            </svg>

        </div>


        <div class="actions">


            <div class="action">

                <div class="action-icon">

                    <svg
                        viewBox="0 0 24 24"
                        fill="currentColor"
                    >
                        <path
                            d="M6 3h12v18l-6-4-6 4z"
                        />
                    </svg>

                </div>

                <div class="action-line"></div>

                <div>

                    <div class="action-title">
                        GUARDA
                    </div>

                    <div class="action-sub">
                        PARA VERLO DESPUÉS
                    </div>

                </div>

            </div>


            <div class="action">

                <div class="action-icon">

                    <svg
                        viewBox="0 0 24 24"
                        fill="currentColor"
                    >
                        <path
                            d="M22 2 9 15l-1 6 4-3 4 4zM2 11l20-9-9 20-3-8z"
                        />
                    </svg>

                </div>

                <div class="action-line"></div>

                <div>

                    <div class="action-title">
                        COMPARTE
                    </div>

                    <div class="action-sub">
                        CON TUS AMIGOS
                    </div>

                </div>

            </div>


            <div class="action">

                <div class="action-icon">

                    <svg
                        viewBox="0 0 24 24"
                        fill="currentColor"
                    >
                        <path
                            d="M4 4h16v12H8l-4 4z"
                        />
                    </svg>

                </div>

                <div class="action-line"></div>

                <div>

                    <div class="action-title">
                        COMENTA
                    </div>

                    <div class="action-sub">
                        TU OPINIÓN
                    </div>

                </div>

            </div>


        </div>

    </section>


    <div class="follow">

        <div class="follow-icon">

            <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.2"
                stroke-linecap="round"
                stroke-linejoin="round"
            >

                <circle
                    cx="9"
                    cy="7"
                    r="4"
                />

                <path
                    d="M2.5 21v-2.2c0-3.2 2.6-5.8 5.8-5.8h1.4c3.2 0 5.8 2.6 5.8 5.8V21"
                />

                <path
                    d="M19 8v6"
                />

                <path
                    d="M16 11h6"
                />

            </svg>

        </div>

        <div class="follow-text">
            SÍGUEME
        </div>

    </div>


    <footer class="footer">

        <div class="footer-top">

            <div class="brand">

                <div class="avatar">

                    <img
                        id="avatar"
                        alt="Nicolas Hernandez"
                    >

                </div>

                <div>

                    <div class="brand-kicker">

                        NOTICIAS / GAMING / TECH / CULTURA POP

                    </div>

                    <div class="brand-name">

                        NICOLAS HERNANDEZ

                        <span>
                            ///
                        </span>

                    </div>

                </div>

            </div>


            <div class="footer-message">

                MÁS NOTICIAS.<br>
                MÁS GAMING.<br>
                MÁS PASIÓN.

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

                    </svg>

                </span>

                <span id="instagram"></span>

            </div>


            <div class="sep"></div>


            <div class="social">

                <span class="social-icon">

                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.2"
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


            <div class="sep"></div>


            <div class="social">

                <span class="social-icon">

                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.2"
                    >

                        <path d="M5 4l14 16"/>
                        <path d="M19 4L5 20"/>

                    </svg>

                </span>

                <span id="x"></span>

            </div>


        </div>

    </footer>


</div>


<script>

const payload =
    __PAYLOAD__;


const avatar =
    document.getElementById(
        "avatar"
    );


if (
    payload.avatar
) {

    avatar.src =
        payload.avatar;

}


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

</script>


</body>

</html>
'''


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    html = HTML.replace(
        "__PAYLOAD__",
        json.dumps(
            payload,
            ensure_ascii=False,
        ),
    )

    TEMP_HTML.write_text(
        html,
        encoding="utf-8",
    )

    print()
    print("=" * 68)
    print(" GENERANDO CTA FINAL GNG")
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

        page.evaluate(
            "() => document.fonts.ready.then(() => true)"
        )

        page.wait_for_timeout(
            300
        )

        image_bytes = (
            page
            .locator(
                ".cta-card"
            )
            .screenshot()
        )

        OUTPUT_FILE.write_bytes(
            image_bytes
        )

        browser.close()

    print(
        "OK - CTA generado:"
    )

    print(
        OUTPUT_FILE
    )

    print()


if __name__ == "__main__":
    main()
