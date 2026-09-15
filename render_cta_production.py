from pathlib import Path
import subprocess
import sys

from PIL import Image


BASE_DIR = Path(__file__).resolve().parent

PERSONAL_CTA = (
    BASE_DIR
    / "assets"
    / "personal"
    / "cta_personal.png"
)

OUTPUT_DIR = (
    BASE_DIR
    / "output"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "07_cta.png"
)

DYNAMIC_RENDERER = (
    BASE_DIR
    / "render_cta.py"
)

TARGET_SIZE = (
    1080,
    1350,
)


def render_personal():
    with Image.open(
        PERSONAL_CTA
    ) as image:

        image.load()

        image = image.convert(
            "RGB"
        )

        if image.size != TARGET_SIZE:
            print(
                "Normalizando CTA personal:",
                f"{image.width}x{image.height}",
                "->",
                "1080x1350",
            )

            image = image.resize(
                TARGET_SIZE,
                Image.Resampling.LANCZOS,
            )

        image.save(
            OUTPUT_FILE,
            format="PNG",
            optimize=True,
        )


def run_dynamic():
    subprocess.run(
        [
            sys.executable,
            str(DYNAMIC_RENDERER),
        ],
        cwd=BASE_DIR,
        check=True,
    )


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 68)
    print(" GENERANDO CTA FINAL")
    print("=" * 68)
    print()

    if PERSONAL_CTA.exists():
        print(
            "CTA personal detectado."
        )

        render_personal()

        print()
        print(
            "Modo usado: CTA FIJO PERSONAL"
        )

    else:
        print(
            "CTA personal no encontrado."
        )

        print(
            "Usando plantilla dinamica."
        )

        run_dynamic()

        print()
        print(
            "Modo usado: CTA DINAMICO"
        )

    if not OUTPUT_FILE.exists():
        raise RuntimeError(
            "No se genero output/07_cta.png"
        )

    if (
        OUTPUT_FILE.stat().st_size
        < 10000
    ):
        raise RuntimeError(
            "07_cta.png parece invalido."
        )

    with Image.open(
        OUTPUT_FILE
    ) as image:

        image.load()

        if image.size != TARGET_SIZE:
            raise RuntimeError(
                "07_cta.png no mide "
                "1080x1350. "
                f"Mide {image.width}x{image.height}."
            )

    print(
        "OK - CTA final:",
        OUTPUT_FILE,
    )

    print(
        "Resolucion: 1080x1350"
    )

    print()


if __name__ == "__main__":
    main()
