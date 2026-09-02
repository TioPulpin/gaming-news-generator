import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable


def run_step(title, script):

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)
    print()

    script_path = BASE_DIR / script

    if not script_path.exists():
        print(f"ERROR: No existe {script}")
        raise SystemExit(1)

    result = subprocess.run(
        [
            PYTHON,
            str(script_path)
        ],
        cwd=str(BASE_DIR)
    )

    if result.returncode != 0:
        print()
        print("!" * 60)
        print(f"ERROR EN: {title}")
        print("!" * 60)
        raise SystemExit(result.returncode)


print()
print("#" * 60)
print("#")
print("#   GAMING NEWS GENERATOR")
print("#   PRUEBA COMPLETA SIN IA")
print("#")
print("#   COSTO API: $0.00")
print("#")
print("#" * 60)


# =========================================================
# PASO 1
# =========================================================

run_step(
    "PASO 1 - VALIDANDO noticias.json",
    "validate_news.py"
)


# =========================================================
# PASO 2
# =========================================================

run_step(
    "PASO 2 - GENERANDO LAS 5 TARJETAS",
    "render_batch.py"
)


# =========================================================
# PASO 3
# =========================================================

run_step(
    "PASO 3 - SUBIENDO A GOOGLE DRIVE",
    "drive_upload.py"
)


print()
print("#" * 60)
print("#")
print("#   PRUEBA COMPLETADA CORRECTAMENTE")
print("#")
print("#   5 TARJETAS GENERADAS")
print("#   5 TARJETAS SUBIDAS / ACTUALIZADAS EN DRIVE")
print("#")
print("#   COSTO API: $0.00")
print("#")
print("#" * 60)
print()