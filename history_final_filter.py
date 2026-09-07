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

HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "published_history.json"
)

EXPECTED_COUNT = 6


def load_json_list(path: Path, label: str) -> list[dict]:
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


def title_of(item: dict) -> str:
    return str(
        item.get("titulo")
        or item.get("title")
        or ""
    ).strip()


def number_of(item: dict) -> str:
    return str(
        item.get("numero")
        or "??"
    ).strip()


def main():
    news = load_json_list(
        NEWS_FILE,
        "noticias.json",
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

    recent_history = get_recent_history(
        history
    )

    print()
    print("=" * 68)
    print(
        " FILTRO FINAL ANTI-REPETICION "
        "- BARRERA DE SEGURIDAD"
    )
    print("=" * 68)
    print()

    print(
        f"Noticias finales: {len(news)}"
    )

    print(
        "Entradas recientes del historial: "
        f"{len(recent_history)}"
    )

    print()

    history_duplicates = []

    # ==================================================
    # 1. COMPARAR CONTRA HISTORIAL
    # ==================================================

    for candidate in news:
        current_title = title_of(
            candidate
        )

        for old_item in recent_history:
            duplicate, reason = compare_story(
                candidate,
                old_item,
            )

            if not duplicate:
                continue

            history_duplicates.append(
                {
                    "numero": number_of(
                        candidate
                    ),
                    "actual": current_title,
                    "anterior": title_of(
                        old_item
                    ),
                    "fecha": str(
                        old_item.get(
                            "date",
                            old_item.get(
                                "fecha",
                                "",
                            ),
                        )
                    ),
                    "motivo": reason,
                }
            )

            # Una coincidencia es suficiente
            # para bloquear esta noticia.
            break

    # ==================================================
    # 2. COMPARAR LAS 6 ENTRE SI
    # ==================================================

    batch_duplicates = []

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

            if not duplicate:
                continue

            batch_duplicates.append(
                {
                    "numero_a": number_of(
                        news[i]
                    ),
                    "titulo_a": title_of(
                        news[i]
                    ),
                    "numero_b": number_of(
                        news[j]
                    ),
                    "titulo_b": title_of(
                        news[j]
                    ),
                    "motivo": reason,
                }
            )

    # ==================================================
    # RESULTADO
    # ==================================================

    if history_duplicates:
        print(
            "DUPLICADOS CONTRA HISTORIAL:"
        )
        print()

        for item in history_duplicates:
            print(
                f'[{item["numero"]}] '
                f'{item["actual"]}'
            )

            print(
                "    Ya publicada: "
                f'{item["fecha"]} | '
                f'{item["anterior"]}'
            )

            print(
                "    Motivo: "
                f'{item["motivo"]}'
            )

            print()

    if batch_duplicates:
        print(
            "DUPLICADOS DENTRO DEL MISMO LOTE:"
        )
        print()

        for item in batch_duplicates:
            print(
                f'[{item["numero_a"]}] '
                f'{item["titulo_a"]}'
            )

            print(
                "    VS"
            )

            print(
                f'[{item["numero_b"]}] '
                f'{item["titulo_b"]}'
            )

            print(
                "    Motivo: "
                f'{item["motivo"]}'
            )

            print()

    total_duplicates = (
        len(history_duplicates)
        + len(batch_duplicates)
    )

    if total_duplicates:
        print("=" * 68)
        print(
            "BLOQUEO DE SEGURIDAD ACTIVADO"
        )
        print("=" * 68)
        print()

        print(
            "El pipeline se detiene antes de "
            "buscar imagenes, renderizar o subir "
            "contenido a Drive."
        )

        print()

        raise RuntimeError(
            "Se detectaron noticias repetidas "
            "en la seleccion editorial final."
        )

    print(
        "OK - Las 6 noticias finales "
        "son nuevas."
    )

    print(
        "OK - No hay historias duplicadas "
        "dentro del mismo lote."
    )

    print()


if __name__ == "__main__":
    main()
