import subprocess
import sys
from pathlib import Path


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

PYTHON = sys.executable

RENDER_SCRIPT = BASE_DIR / "render_batch.py"
UPLOAD_SCRIPT = BASE_DIR / "drive_upload.py"


# =========================================================
# UTILIDAD PARA EJECUTAR PASOS
# =========================================================

def ejecutar(nombre, script):

    print()
    print("==============================================")
    print(f" {nombre}")
    print("==============================================")
    print()

    resultado = subprocess.run(
        [
            PYTHON,
            str(script)
        ],
        cwd=str(BASE_DIR)
    )

    if resultado.returncode != 0:

        print()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f" ERROR EN: {nombre}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print()

        sys.exit(
            resultado.returncode
        )


# =========================================================
# INICIO
# =========================================================

print()
print("################################################")
print("#                                              #")
print("#       GAMING NEWS GENERATOR                  #")
print("#       NICOLAS HERNANDEZ                      #")
print("#                                              #")
print("################################################")
print()


# =========================================================
# PASO 1
# =========================================================

ejecutar(
    "PASO 1 - GENERANDO LAS 5 TARJETAS",
    RENDER_SCRIPT
)


# =========================================================
# PASO 2
# =========================================================

ejecutar(
    "PASO 2 - SUBIENDO A GOOGLE DRIVE",
    UPLOAD_SCRIPT
)


# =========================================================
# FINAL
# =========================================================

print()
print("################################################")
print("#                                              #")
print("#          PROCESO COMPLETADO                  #")
print("#                                              #")
print("#     5 TARJETAS GENERADAS Y SUBIDAS           #")
print("#                                              #")
print("################################################")
print()