from pathlib import Path

from PIL import Image


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

TARGET_SIZE = (
    1080,
    1350,
)

MIN_SIZE = 10000


def validate_png(
    path: Path,
):
    if not path.exists():
        return (
            False,
            "archivo inexistente",
        )

    if (
        path.stat().st_size
        < MIN_SIZE
    ):
        return (
            False,
            "archivo demasiado pequeno",
        )

    try:
        with Image.open(
            path
        ) as image:

            image.load()

            if image.format != "PNG":
                return (
                    False,
                    f"formato {image.format}",
                )

            if image.size != TARGET_SIZE:
                return (
                    False,
                    (
                        f"{image.width}x"
                        f"{image.height}; "
                        "se esperaba 1080x1350"
                    ),
                )

    except Exception as exc:
        return (
            False,
            f"imagen invalida: {exc}",
        )

    return (
        True,
        "1080x1350",
    )


def resolve_expected():
    files = []

    cover = (
        OUTPUT_DIR
        / "00_cover.png"
    )

    files.append(
        (
            "00",
            cover,
        )
    )

    for numero in range(
        1,
        7,
    ):
        key = f"{numero:02d}"

        matches = sorted(
            OUTPUT_DIR.glob(
                f"{key}_*.png"
            )
        )

        if len(matches) != 1:
            files.append(
                (
                    key,
                    None,
                )
            )
        else:
            files.append(
                (
                    key,
                    matches[0],
                )
            )

    cta = (
        OUTPUT_DIR
        / "07_cta.png"
    )

    files.append(
        (
            "07",
            cta,
        )
    )

    return files


def main():
    print()
    print("=" * 68)
    print(" VALIDACION FINAL DEL CARRUSEL")
    print("=" * 68)
    print()

    expected = resolve_expected()

    problems = []

    for numero, path in expected:
        if path is None:
            print(
                f"[{numero}] ERROR: "
                "no existe exactamente "
                "una pieza."
            )

            problems.append(
                f"{numero}: cantidad invalida"
            )

            continue

        ok, detail = validate_png(
            path
        )

        if ok:
            print(
                f"[{numero}] OK - "
                f"{path.name} - "
                f"{detail}"
            )
        else:
            print(
                f"[{numero}] ERROR - "
                f"{path.name} - "
                f"{detail}"
            )

            problems.append(
                f"{numero}: {detail}"
            )

    print()

    if problems:
        print("=" * 68)
        print(
            " CARRUSEL BLOQUEADO"
        )
        print("=" * 68)

        raise RuntimeError(
            "Hay piezas invalidas: "
            + " | ".join(
                problems
            )
        )

    print("=" * 68)
    print(
        " 8/8 PIEZAS VALIDAS - "
        "SUBIDA AUTORIZADA"
    )
    print("=" * 68)
    print()


if __name__ == "__main__":
    main()
