import json
from pathlib import Path

from history_filter import (
    compare_story,
    get_recent_history,
)


BASE_DIR = Path(__file__).resolve().parent

NEWS_FILE = (
    BASE_DIR
    / "data"
    / "noticias.json"
)

RESERVES_FILE = (
    BASE_DIR
    / "data"
    / "editorial_reserves.json"
)

HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "published_history.json"
)

EXPECTED_COUNT = 6
EXPECTED_RESERVES = 3

VALID_BRANCHES = {
    "gaming",
    "tecnologia",
    "cultura_pop",
}


def load_json_list(
    path: Path,
    label: str,
) -> list[dict]:

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
        raise ValueError(
            f"{label} debe contener una lista JSON."
        )

    return data


def title_of(
    item: dict,
) -> str:

    return str(
        item.get("titulo")
        or item.get("title")
        or ""
    ).strip()


def number_of(
    item: dict,
) -> str:

    return str(
        item.get("numero")
        or "??"
    ).strip()


def branch_of(
    item: dict,
) -> str:

    return str(
        item.get("rama")
        or item.get("editorial_branch")
        or ""
    ).strip()


def date_of(
    item: dict,
) -> str:

    return str(
        item.get("date")
        or item.get("fecha")
        or ""
    ).strip()


def find_history_duplicate(
    candidate: dict,
    recent_history: list[dict],
) -> tuple[dict | None, str]:

    for old_item in recent_history:
        duplicate, reason = compare_story(
            candidate,
            old_item,
        )

        if duplicate:
            return old_item, reason

    return None, ""


def find_batch_duplicate(
    candidate: dict,
    accepted: list[dict],
) -> tuple[dict | None, str]:

    for other in accepted:
        duplicate, reason = compare_story(
            candidate,
            other,
        )

        if duplicate:
            return other, reason

    return None, ""


def is_clean_candidate(
    candidate: dict,
    recent_history: list[dict],
    accepted: list[dict],
) -> tuple[bool, str]:

    old_item, reason = find_history_duplicate(
        candidate,
        recent_history,
    )

    if old_item is not None:
        message = (
            "repite historial: "
            f"{date_of(old_item)} | "
            f"{title_of(old_item)}"
        )

        if reason:
            message += f" | {reason}"

        return False, message

    other, reason = find_batch_duplicate(
        candidate,
        accepted,
    )

    if other is not None:
        message = (
            "repite otra noticia del lote: "
            f"{number_of(other)} | "
            f"{title_of(other)}"
        )

        if reason:
            message += f" | {reason}"

        return False, message

    return True, ""


def validate_reserves(
    reserves: list[dict],
):

    if len(reserves) != EXPECTED_RESERVES:
        raise ValueError(
            "Se esperaban "
            f"{EXPECTED_RESERVES} reservas "
            f"y se encontraron {len(reserves)}."
        )

    counts = {
        "gaming": 0,
        "tecnologia": 0,
        "cultura_pop": 0,
    }

    for reserve in reserves:
        branch = branch_of(
            reserve
        )

        if branch not in VALID_BRANCHES:
            raise ValueError(
                "Reserva con rama invalida: "
                f"{branch!r}"
            )

        counts[
            branch
        ] += 1

    expected = {
        "gaming": 1,
        "tecnologia": 1,
        "cultura_pop": 1,
    }

    if counts != expected:
        raise ValueError(
            "Distribucion de reservas "
            f"invalida: {counts}"
        )


def choose_reserve(
    branch: str,
    reserves: list[dict],
    used_reserve_indexes: set[int],
    recent_history: list[dict],
    accepted: list[dict],
) -> tuple[dict | None, int | None, str]:

    reasons = []

    for index, reserve in enumerate(
        reserves
    ):
        if index in used_reserve_indexes:
            continue

        if branch_of(
            reserve
        ) != branch:
            continue

        clean, reason = is_clean_candidate(
            reserve,
            recent_history,
            accepted,
        )

        if clean:
            return reserve, index, ""

        reasons.append(
            f"{title_of(reserve)} -> {reason}"
        )

    if reasons:
        return (
            None,
            None,
            "La reserva disponible tampoco es valida: "
            + " || ".join(reasons),
        )

    return (
        None,
        None,
        "No hay una reserva disponible "
        f"para la rama {branch}.",
    )


def final_safety_check(
    news: list[dict],
    recent_history: list[dict],
):

    problems = []

    for candidate in news:
        old_item, reason = find_history_duplicate(
            candidate,
            recent_history,
        )

        if old_item is not None:
            problems.append(
                (
                    f'[{number_of(candidate)}] '
                    f'{title_of(candidate)} '
                    "repite historial: "
                    f'{date_of(old_item)} | '
                    f'{title_of(old_item)} | '
                    f'{reason}'
                )
            )

    for i in range(
        len(news)
    ):
        for j in range(
            i + 1,
            len(news),
        ):
            duplicate, reason = compare_story(
                news[i],
                news[j],
            )

            if duplicate:
                problems.append(
                    (
                        f'[{number_of(news[i])}] '
                        f'{title_of(news[i])} '
                        "VS "
                        f'[{number_of(news[j])}] '
                        f'{title_of(news[j])} '
                        f'| {reason}'
                    )
                )

    return problems


def main():
    news = load_json_list(
        NEWS_FILE,
        "noticias.json",
    )

    reserves = load_json_list(
        RESERVES_FILE,
        "editorial_reserves.json",
    )

    history = load_json_list(
        HISTORY_FILE,
        "published_history.json",
    )

    if len(news) != EXPECTED_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_COUNT} noticias "
            f"y se encontraron {len(news)}."
        )

    validate_reserves(
        reserves
    )

    recent_history = get_recent_history(
        history
    )

    print()
    print("=" * 72)
    print(
        " FILTRO FINAL ANTI-REPETICION "
        "- SUSTITUCION AUTOMATICA"
    )
    print("=" * 72)
    print()

    print(
        f"Noticias principales: {len(news)}"
    )

    print(
        f"Reservas disponibles: {len(reserves)}"
    )

    print(
        "Entradas recientes del historial: "
        f"{len(recent_history)}"
    )

    print()

    final_news = []
    used_reserve_indexes = set()
    replacements = []

    # =====================================================
    # EVALUAR LAS 6 PRINCIPALES
    # =====================================================

    for original in news:
        clean, reason = is_clean_candidate(
            original,
            recent_history,
            final_news,
        )

        if clean:
            final_news.append(
                original
            )

            print(
                f'OK [{number_of(original)}] '
                f'{title_of(original)}'
            )

            continue

        print()
        print(
            f'REPETIDA [{number_of(original)}] '
            f'{title_of(original)}'
        )

        print(
            f"    Motivo: {reason}"
        )

        branch = branch_of(
            original
        )

        if branch not in VALID_BRANCHES:
            raise RuntimeError(
                "No se puede buscar reserva: "
                f"rama invalida {branch!r}."
            )

        reserve, reserve_index, reserve_error = (
            choose_reserve(
                branch,
                reserves,
                used_reserve_indexes,
                recent_history,
                final_news,
            )
        )

        if reserve is None:
            print()
            print("=" * 72)
            print(
                "BLOQUEO DE SEGURIDAD ACTIVADO"
            )
            print("=" * 72)
            print()

            print(
                "No fue posible reemplazar "
                "automaticamente la noticia."
            )

            print(
                f"Motivo: {reserve_error}"
            )

            print()

            raise RuntimeError(
                "No existe una reserva valida "
                "para sustituir una noticia repetida."
            )

        replacement = dict(
            reserve
        )

        # La sustituta ocupa exactamente
        # la posicion de la noticia original.
        replacement[
            "numero"
        ] = number_of(
            original
        )

        used_reserve_indexes.add(
            reserve_index
        )

        final_news.append(
            replacement
        )

        replacements.append(
            {
                "numero": number_of(
                    original
                ),
                "rama": branch,
                "original": title_of(
                    original
                ),
                "reemplazo": title_of(
                    replacement
                ),
            }
        )

        print(
            "    REEMPLAZADA POR:"
        )

        print(
            f'    [{number_of(replacement)}] '
            f'{title_of(replacement)}'
        )

        print()

    # =====================================================
    # BARRERA FINAL DESPUES DE LOS REEMPLAZOS
    # =====================================================

    problems = final_safety_check(
        final_news,
        recent_history,
    )

    if problems:
        print()
        print("=" * 72)
        print(
            "BLOQUEO FINAL DE SEGURIDAD"
        )
        print("=" * 72)
        print()

        for problem in problems:
            print(
                f"- {problem}"
            )

        print()

        raise RuntimeError(
            "La seleccion final sigue conteniendo "
            "una historia repetida."
        )

    # =====================================================
    # GUARDAR LAS 6 DEFINITIVAS
    # =====================================================

    NEWS_FILE.write_text(
        json.dumps(
            final_news,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print(
        " RESULTADO FINAL"
    )
    print("=" * 72)
    print()

    if replacements:
        print(
            "Sustituciones realizadas:"
        )
        print()

        for item in replacements:
            print(
                f'[{item["numero"]}] '
                f'[{item["rama"]}]'
            )

            print(
                "    Original: "
                f'{item["original"]}'
            )

            print(
                "    Reserva:  "
                f'{item["reemplazo"]}'
            )

            print()

    else:
        print(
            "No fue necesario utilizar reservas."
        )
        print()

    print(
        "OK - Las 6 noticias definitivas "
        "son nuevas."
    )

    print(
        "OK - No existen duplicados "
        "dentro del lote."
    )

    print(
        "OK - noticias.json actualizado."
    )

    print()


if __name__ == "__main__":
    main()
