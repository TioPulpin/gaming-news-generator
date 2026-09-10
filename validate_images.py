from pathlib import Path
import json

from PIL import Image


BASE_DIR = Path(__file__).resolve().parent
NEWS_FILE = BASE_DIR / "data" / "noticias.json"

EXPECTED_NEWS = 6
MIN_WIDTH = 600
MIN_HEIGHT = 338
MIN_FILE_SIZE = 20_000


def validate_image(path: Path):
    if not path.exists():
        return False, f"archivo inexistente: {path}"

    if not path.is_file():
        return False, f"no es un archivo: {path}"

    size = path.stat().st_size

    if size < MIN_FILE_SIZE:
        return False, f"archivo demasiado pequeño: {size} bytes"

    try:
        with Image.open(path) as image:
            image.load()

            width, height = image.size

            if width < MIN_WIDTH or height < MIN_HEIGHT:
                return (
                    False,
                    f"dimensiones insuficientes: {width}x{height}",
                )

    except Exception as error:
        return False, f"imagen inválida: {error}"

    return True, f"{width}x{height}"


def main():
    if not NEWS_FILE.exists():
        raise FileNotFoundError(
            f"No existe: {NEWS_FILE}"
        )

    news = json.loads(
        NEWS_FILE.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(news, list):
        raise RuntimeError(
            "data/noticias.json no contiene una lista."
        )

    if len(news) != EXPECTED_NEWS:
        raise RuntimeError(
            f"Se esperaban {EXPECTED_NEWS} noticias "
            f"y existen {len(news)}."
        )

    errors = []

    print()
    print("=" * 68)
    print(" VALIDACION FINAL DE IMAGENES")
    print("=" * 68)
    print()

    for item in news:
        numero = str(
            item.get("numero", "?")
        ).zfill(2)

        titulo = str(
            item.get("titulo", "")
        ).strip()

        image_value = str(
            item.get("imagen", "")
        ).strip()

        print(
            f"[{numero}] {titulo[:70]}"
        )

        if not image_value:
            errors.append(
                f"[{numero}] campo 'imagen' vacío"
            )

            print(
                "     ERROR: campo imagen vacío"
            )
            continue

        image_path = Path(
            image_value
        )

        if not image_path.is_absolute():
            image_path = (
                BASE_DIR
                / image_path
            )

        ok, detail = validate_image(
            image_path
        )

        if not ok:
            errors.append(
                f"[{numero}] {detail}"
            )

            print(
                f"     ERROR: {detail}"
            )
            continue

        print(
            f"     OK: {detail}"
        )

    print()
    print("=" * 68)

    if errors:
        print(
            " BLOQUEO DE SEGURIDAD: "
            "NO SE PUEDE RENDERIZAR"
        )
        print("=" * 68)
        print()

        for error in errors:
            print(
                " -",
                error,
            )

        print()
        raise RuntimeError(
            f"Faltan imágenes válidas "
            f"en {len(errors)} tarjeta(s)."
        )

    print(
        " 6/6 IMAGENES VALIDAS - "
        "RENDER AUTORIZADO"
    )
    print("=" * 68)
    print()


if __name__ == "__main__":
    main()
