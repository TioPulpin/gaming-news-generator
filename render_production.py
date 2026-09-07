import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(
    __file__
).resolve().parent

OUTPUT_DIR = (
    BASE_DIR
    / "output"
)

EXPECTED_NUMBERS = [
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
]


def clean_cards():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    removed = 0

    for path in OUTPUT_DIR.glob(
        "[0-9][0-9]_*.png"
    ):

        path.unlink()

        removed += 1

    print(
        "Tarjetas antiguas eliminadas:",
        removed,
    )


def run_renderer(
    filename: str,
):

    print()
    print(
        "Ejecutando:",
        filename,
    )
    print()

    subprocess.run(
        [
            sys.executable,
            str(
                BASE_DIR
                / filename
            ),
        ],
        cwd=str(
            BASE_DIR
        ),
        check=True,
    )


def validate_cards():

    problems = []

    cards = []

    for numero in EXPECTED_NUMBERS:

        matches = sorted(
            OUTPUT_DIR.glob(
                f"{numero}_*.png"
            )
        )

        if len(matches) != 1:

            problems.append(
                f"{numero}: "
                f"{len(matches)} archivos"
            )

            continue

        card = matches[0]

        if (
            not card.exists()
            or card.stat().st_size < 10000
        ):

            problems.append(
                f"{numero}: archivo invalido"
            )

            continue

        cards.append(
            card
        )


    if problems:

        raise RuntimeError(
            "Validacion de tarjetas fallida: "
            + " | ".join(
                problems
            )
        )


    if len(cards) != 6:

        raise RuntimeError(
            "No existen exactamente "
            "6 tarjetas validas."
        )


    return cards


def main():

    print()
    print("=" * 68)
    print(
        " RENDER DE PRODUCCION "
        "- V2 CON FALLBACK V1"
    )
    print("=" * 68)
    print()


    # =====================================================
    # INTENTO V2
    # =====================================================

    clean_cards()

    try:

        run_renderer(
            "render_batch_v2_production.py"
        )

        cards = validate_cards()

        print()
        print("=" * 68)
        print(
            " TEMPLATE V2 SELECCIONADO"
        )
        print("=" * 68)

        for card in cards:
            print(
                card.name
            )

        print()

        return


    except Exception as exc:

        print()
        print("=" * 68)
        print(
            " V2 FALLO - ACTIVANDO V1"
        )
        print("=" * 68)
        print()

        print(
            "Motivo:",
            exc,
        )

        print()


    # =====================================================
    # FALLBACK V1
    # =====================================================

    clean_cards()

    run_renderer(
        "render_batch.py"
    )

    cards = validate_cards()

    print()
    print("=" * 68)
    print(
        " FALLBACK V1 COMPLETADO"
    )
    print("=" * 68)

    for card in cards:
        print(
            card.name
        )

    print()


if __name__ == "__main__":
    main()
