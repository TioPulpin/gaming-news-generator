import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


BASE_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable

CONFIG_FILE = BASE_DIR / "ai_config.json"

RUN_STATE_FILE = (
    BASE_DIR
    / "data"
    / "last_successful_run.json"
)


def lima_now():
    if ZoneInfo is not None:
        try:
            return datetime.now(
                ZoneInfo("America/Lima")
            )
        except Exception:
            pass

    return datetime.now()


def lima_today():
    return lima_now().strftime(
        "%Y-%m-%d"
    )


def load_run_state():
    if not RUN_STATE_FILE.exists():
        return {}

    try:
        data = json.loads(
            RUN_STATE_FILE.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def already_generated_today():
    state = load_run_state()

    return (
        state.get("date") == lima_today()
        and state.get("status") == "completed"
    )


def print_already_generated():
    print()
    print("=" * 64)
    print(
        " GNG - CONTROL DE EJECUCION DIARIA "
    )
    print("=" * 64)
    print()
    print(
        f"Fecha: {lima_today()}"
    )
    print(
        "Estado: YA GENERADO"
    )
    print()
    print(
        "Las noticias de hoy ya fueron "
        "generadas correctamente."
    )
    print(
        "No se ejecutara nuevamente "
        "el pipeline."
    )
    print(
        "Costo adicional: $0.00"
    )
    print()


def mark_daily_success():
    RUN_STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    now = lima_now()

    state = {
        "date": now.strftime(
            "%Y-%m-%d"
        ),
        "status": "completed",
        "completed_at": now.isoformat(),
    }

    RUN_STATE_FILE.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "Ejecucion diaria marcada "
        "como completada."
    )
    print(
        f"Fecha bloqueada: "
        f"{state['date']}"
    )


def run_step(title, script):
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)
    print()

    script_path = (
        BASE_DIR / script
    )

    if not script_path.exists():
        print(
            f"ERROR: No existe {script}"
        )
        raise SystemExit(1)

    result = subprocess.run(
        [
            PYTHON,
            str(script_path),
        ],
        cwd=str(BASE_DIR),
    )

    if result.returncode != 0:
        print()
        print("!" * 64)
        print(
            f"ERROR EN: {title}"
        )
        print("!" * 64)
        raise SystemExit(
            result.returncode
        )


def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            "No existe ai_config.json."
        )

    return json.loads(
        CONFIG_FILE.read_text(
            encoding="utf-8"
        )
    )


def main():
    if already_generated_today():
        print_already_generated()
        return

    config = load_config()

    api_enabled = bool(
        config.get(
            "api_enabled",
            False,
        )
    )

    print()
    print("#" * 64)
    print("#")
    print("#   NICOLAS HERNANDEZ - NEWS GENERATOR")
    print("#   PIPELINE DIARIO MULTITEMÃTICO V3")
    print("#")
    print(
        f"#   API habilitada: "
        f"{api_enabled}"
    )
    print("#")
    print(
        "#   Objetivo: "
        "6 tarjetas"
    )
    print(
        "#   Gaming + TecnologÃ­a + Cultura Pop"
    )
    print("#")
    print("#" * 64)

    # =====================================================
    # PASO 1
    # =====================================================

    run_step(
        "PASO 1 - INVESTIGACIÃ“N MULTITEMÃTICA",
        "fetch_news.py",
    )

    # =====================================================
    # PASO 1.5 - FILTRO ANTI-REPETICIÃ“N
    # =====================================================

    run_step(
        "PASO 1.5 - FILTRO ANTI-REPETICIÃ“N",
        "history_filter.py",
    )

    # =====================================================
    # PASO 2
    # =====================================================

    run_step(
        "PASO 2 - RANKING MULTITEMÃTICO GRATIS",
        "rank_candidates.py",
    )

    # =====================================================
    # PASO 3
    # =====================================================

    run_step(
        "PASO 3 - EDITORIAL FINAL",
        "editorial_final.py",
    )

    # =====================================================
    # API APAGADA = DETENER
    # =====================================================

    if not api_enabled:
        print()
        print("#" * 64)
        print("#")
        print("#   MODO PRUEBA COMPLETADO")
        print("#")
        print(
            "#   InvestigaciÃ³n multitemÃ¡tica  OK"
        )
        print(
            "#   Ranking 8 + 8 + 8            OK"
        )
        print(
            "#   24 candidatas preparadas     OK"
        )
        print(
            "#   Terra NO ejecutado"
        )
        print(
            "#   Costo OpenAI API: $0.00"
        )
        print("#")
        print(
            "#   El pipeline se detiene aquÃ­"
        )
        print(
            "#   porque api_enabled = false."
        )
        print("#")
        print("#" * 64)
        print()
        return

    # =====================================================
    # PASO 4
    # =====================================================

    run_step(
        "PASO 4 - VALIDANDO LAS 6 NOTICIAS",
        "validate_news.py",
    )

    # =====================================================
    # PASO 4.5
    # =====================================================

    run_step(
        "PASO 4.5 - FILTRO FINAL ANTI-REPETICION",
        "history_final_filter.py",
    )

    # =====================================================
    # PASO 5
    # =====================================================

    run_step(
        "PASO 5 - RESOLVIENDO IMÃGENES",
        "resolve_images.py",
    )

    # =====================================================
    # PASO 6
    # =====================================================

    run_step(
        "PASO 6 - DESCARGANDO Y NORMALIZANDO IMÃGENES",
        "download_images.py",
    )

    # =====================================================
    # PASO 6.25 - RECUPERACION AUTOMATICA DE IMAGENES
    # =====================================================

    run_step(
        "PASO 6.25 - RECUPERANDO FALLOS DE IMAGEN",
        "recover_missing_images.py",
    )

    # =====================================================
    # PASO 6.5 - SEGURIDAD DE IMAGENES
    # =====================================================

    run_step(
        "PASO 6.5 - VALIDANDO 6 IMAGENES",
        "validate_images.py",
    )

    # =====================================================
    # PASO 7
    # =====================================================

    run_step(
        "PASO 7 - GENERANDO 6 TARJETAS - V2 CON FALLBACK V1",
        "render_production.py",
    )

    # =====================================================
    # PASO 7.25 - PORTADA
    # =====================================================

    run_step(
        "PASO 7.25 - GENERANDO PORTADA DEL CARRUSEL",
        "render_cover.py",
    )

    # =====================================================
    # PASO 7.5 - CTA FINAL
    # =====================================================

    run_step(
        "PASO 7.5 - GENERANDO CTA FINAL",
        "render_cta_production.py",
    )

    # =====================================================
    # PASO 7.75 - VALIDACION DEL CARRUSEL
    # =====================================================

    run_step(
        "PASO 7.75 - VALIDANDO 8 PIEZAS DEL CARRUSEL",
        "validate_carousel.py",
    )

    # =====================================================
    # PASO 8
    # =====================================================

    run_step(
        "PASO 8 - SUBIENDO 8 PIEZAS A GOOGLE DRIVE",
        "drive_upload.py",
    )

    # =====================================================
    # PASO 9 - REGISTRO DE HISTORIAL
    # =====================================================

    run_step(
        "PASO 9 - REGISTRANDO NOTICIAS PUBLICADAS",
        "history_register.py",
    )

    # =====================================================
    # PASO 10
    # =====================================================

    run_step(
        "PASO 10 - RESUMEN DE PRESUPUESTO",
        "api_budget.py",
    )

    # =====================================================
    # BLOQUEO ANTI-DOBLE GENERACION
    # =====================================================

    mark_daily_success()

    print()
    print("#" * 64)
    print("#")
    print("#   PIPELINE DIARIO COMPLETADO")
    print("#")
    print(
        "#   6 noticias finales"
    )
    print(
        "#   6 imÃ¡genes reales de Internet"
    )
    print(
        "#   6 tarjetas 1080 x 1350"
    )
    print(
        "#   Google Drive actualizado"
    )
    print("#")
    print("#" * 64)
    print()


if __name__ == "__main__":
    main()
