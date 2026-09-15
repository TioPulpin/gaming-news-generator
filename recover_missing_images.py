from pathlib import Path
import json
import subprocess
import sys

from history_filter import get_recent_history
from history_final_filter import (
    branch_of,
    choose_reserve,
    validate_reserves,
)
from validate_images import validate_image


BASE_DIR = Path(__file__).resolve().parent

NEWS_FILE = BASE_DIR / "data" / "noticias.json"
RESERVES_FILE = BASE_DIR / "data" / "editorial_reserves.json"
HISTORY_FILE = BASE_DIR / "data" / "published_history.json"

EXPECTED_NEWS = 6


def load_list(path: Path, label: str):
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {label}: {path}"
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(data, list):
        raise RuntimeError(
            f"{label} no contiene una lista."
        )

    return data


def number_of(item: dict, fallback: int):
    value = str(
        item.get("numero", "")
    ).strip()

    if value:
        return value.zfill(2)

    return str(fallback).zfill(2)


def image_status(item: dict):
    image_value = str(
        item.get("imagen", "")
    ).strip()

    if not image_value:
        return False, "campo imagen vacio"

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

    return ok, detail


def clear_image_data(item: dict):
    result = dict(item)

    result["imagen"] = ""
    result["imagenFuente"] = ""
    result["imagenFuenteUrl"] = ""
    result["imagenTipo"] = ""

    return result


def run_child(script_name: str):
    script = BASE_DIR / script_name

    print()
    print(
        f"Ejecutando nuevamente {script_name}..."
    )
    print()

    subprocess.run(
        [
            sys.executable,
            str(script),
        ],
        cwd=BASE_DIR,
        check=True,
    )


def main():
    news = load_list(
        NEWS_FILE,
        "noticias.json",
    )

    reserves = load_list(
        RESERVES_FILE,
        "editorial_reserves.json",
    )

    history = load_list(
        HISTORY_FILE,
        "published_history.json",
    )

    if len(news) != EXPECTED_NEWS:
        raise RuntimeError(
            f"Se esperaban {EXPECTED_NEWS} noticias "
            f"y existen {len(news)}."
        )

    validate_reserves(
        reserves
    )

    failures = []

    print()
    print("=" * 72)
    print(" RECUPERACION AUTOMATICA DE IMAGENES")
    print("=" * 72)
    print()

    for index, item in enumerate(
        news,
        start=1,
    ):
        ok, detail = image_status(
            item
        )

        numero = number_of(
            item,
            index,
        )

        if ok:
            print(
                f"[{numero}] OK"
            )
            continue

        print(
            f"[{numero}] FALLO: {detail}"
        )

        failures.append(
            (
                index - 1,
                item,
                detail,
            )
        )

    if not failures:
        print()
        print(
            "6/6 imagenes validas. "
            "No se necesita recuperacion."
        )
        print()

        return

    recent_history = get_recent_history(
        history
    )

    failed_indexes = {
        index
        for index, _, _ in failures
    }

    # Las noticias sanas ya forman parte
    # del lote final y deben protegerse
    # contra duplicados.
    accepted = [
        item
        for index, item in enumerate(news)
        if index not in failed_indexes
    ]

    # Una reserva puede haber sido utilizada
    # previamente por history_final_filter.py.
    # Si su candidate_id ya esta en noticias.json,
    # la consideramos consumida.
    current_candidate_ids = {
        item.get("candidate_id")
        for item in news
        if item.get("candidate_id") is not None
    }

    used_reserve_indexes = {
        index
        for index, reserve in enumerate(reserves)
        if (
            reserve.get("candidate_id")
            is not None
            and reserve.get("candidate_id")
            in current_candidate_ids
        )
    }

    replacements = []

    for news_index, original, reason in failures:
        branch = branch_of(
            original
        )

        numero = number_of(
            original,
            news_index + 1,
        )

        print()
        print(
            f"Buscando reserva para [{numero}] "
            f"rama={branch}..."
        )

        reserve, reserve_index, reserve_error = (
            choose_reserve(
                branch,
                reserves,
                used_reserve_indexes,
                recent_history,
                accepted,
            )
        )

        if reserve is None:
            raise RuntimeError(
                f"No existe una reserva valida "
                f"para [{numero}] {branch}. "
                f"Motivo: {reserve_error}"
            )

        replacement = clear_image_data(
            reserve
        )

        replacement[
            "numero"
        ] = numero

        news[
            news_index
        ] = replacement

        used_reserve_indexes.add(
            reserve_index
        )

        accepted.append(
            replacement
        )

        replacements.append({
            "numero": numero,
            "rama": branch,
            "original": str(
                original.get(
                    "titulo",
                    "",
                )
            ),
            "reemplazo": str(
                replacement.get(
                    "titulo",
                    "",
                )
            ),
            "motivo": reason,
        })

        print(
            "  Original:",
            original.get(
                "titulo",
                "",
            ),
        )

        print(
            "  Reserva: ",
            replacement.get(
                "titulo",
                "",
            ),
        )

    NEWS_FILE.write_text(
        json.dumps(
            news,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print(
        f" Sustituciones realizadas: "
        f"{len(replacements)}"
    )
    print("=" * 72)

    # El resolver normal ya prueba:
    # articulo original + Google News + Bing.
    # Si llegamos aqui, repetir la noticia
    # original no aporta nada.
    #
    # Resolvemos nuevamente el lote con
    # la noticia de reserva ya colocada.
    run_child(
        "resolve_images.py"
    )

    run_child(
        "download_images.py"
    )

    print()
    print("=" * 72)
    print(
        " RECUPERACION TERMINADA"
    )
    print("=" * 72)

    for item in replacements:
        print()
        print(
            f'[{item["numero"]}] '
            f'{item["original"]}'
        )
        print(
            "    -> "
            f'{item["reemplazo"]}'
        )

    print()
    print(
        "El pipeline puede continuar "
        "con validate_images.py."
    )
    print()


if __name__ == "__main__":
    main()
