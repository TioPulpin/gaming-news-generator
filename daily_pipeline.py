import json
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable

CONFIG_FILE = BASE_DIR / "ai_config.json"


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
    print("#   PIPELINE DIARIO MULTITEMÁTICO V3")
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
        "#   Gaming + Tecnología + Cultura Pop"
    )
    print("#")
    print("#" * 64)

    # =====================================================
    # PASO 1
    # =====================================================

    run_step(
        "PASO 1 - INVESTIGACIÓN MULTITEMÁTICA",
        "fetch_news.py",
    )

    # =====================================================
    # PASO 2
    # =====================================================

    run_step(
        "PASO 2 - RANKING MULTITEMÁTICO GRATIS",
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
            "#   Investigación multitemática  OK"
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
            "#   El pipeline se detiene aquí"
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
    # PASO 5
    # =====================================================

    run_step(
        "PASO 5 - RESOLVIENDO IMÁGENES",
        "resolve_images.py",
    )

    # =====================================================
    # PASO 6
    # =====================================================

    run_step(
        "PASO 6 - DESCARGANDO Y NORMALIZANDO IMÁGENES",
        "download_images.py",
    )

    # =====================================================
    # PASO 7
    # =====================================================

    run_step(
        "PASO 7 - GENERANDO 6 TARJETAS",
        "render_batch.py",
    )

    # =====================================================
    # PASO 8
    # =====================================================

    run_step(
        "PASO 8 - SUBIENDO A GOOGLE DRIVE",
        "drive_upload.py",
    )

    # =====================================================
    # PASO 9
    # =====================================================

    run_step(
        "PASO 9 - RESUMEN DE PRESUPUESTO",
        "api_budget.py",
    )

    print()
    print("#" * 64)
    print("#")
    print("#   PIPELINE DIARIO COMPLETADO")
    print("#")
    print(
        "#   6 noticias finales"
    )
    print(
        "#   6 imágenes reales de Internet"
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
