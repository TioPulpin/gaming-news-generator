import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
NEWS_FILE = BASE_DIR / "data" / "noticias.json"

EXPECTED_COUNT = 6

REQUIRED_FIELDS = [
    "numero",
    "categoria",
    "rama",
    "fecha",
    "titulo",
    "tituloDestacado",
    "resumen",
    "resumenDestacado",
    "imagen",
    "fuente",
    "url",
    "fecha_original",
    "por_que_importa",
    "anguloShort",
    "imagenFuente",
    "imagenFuenteUrl",
    "imagenTipo",
]

VALID_BRANCHES = {
    "gaming",
    "tecnologia",
    "cultura_pop",
}


def fail(message):
    raise ValueError(message)


def main():
    if not NEWS_FILE.exists():
        fail(
            f"No existe el archivo: {NEWS_FILE}"
        )

    news = json.loads(
        NEWS_FILE.read_text(
            encoding="utf-8"
        )
    )

    print()
    print("=" * 60)
    print(" VALIDANDO NOTICIAS V2 - 6 TARJETAS")
    print("=" * 60)
    print()

    if not isinstance(news, list):
        fail(
            "noticias.json debe contener una lista."
        )

    if len(news) != EXPECTED_COUNT:
        fail(
            f"Se esperaban {EXPECTED_COUNT} noticias "
            f"y se encontraron {len(news)}."
        )

    seen_numbers = set()

    branch_counts = {
        "gaming": 0,
        "tecnologia": 0,
        "cultura_pop": 0,
    }

    for index, item in enumerate(
        news,
        start=1,
    ):
        if not isinstance(item, dict):
            fail(
                f"La noticia {index} no es un objeto JSON."
            )

        missing = [
            field
            for field in REQUIRED_FIELDS
            if field not in item
        ]

        if missing:
            fail(
                f"La noticia {index} no tiene los campos: "
                + ", ".join(missing)
            )

        expected_number = f"{index:02d}"

        if item["numero"] != expected_number:
            fail(
                f"La noticia {index} tiene numero="
                f'{item["numero"]!r}; '
                f"se esperaba {expected_number!r}."
            )

        if item["numero"] in seen_numbers:
            fail(
                f"Número duplicado: {item['numero']}"
            )

        seen_numbers.add(
            item["numero"]
        )

        branch = item.get(
            "rama",
            ""
        )

        if branch not in VALID_BRANCHES:
            fail(
                f"La noticia {item['numero']} tiene "
                f"rama inválida: {branch!r}"
            )

        branch_counts[
            branch
        ] += 1

        title = str(
            item.get(
                "titulo",
                ""
            )
        ).strip()

        summary = str(
            item.get(
                "resumen",
                ""
            )
        ).strip()

        category = str(
            item.get(
                "categoria",
                ""
            )
        ).strip()

        source = str(
            item.get(
                "fuente",
                ""
            )
        ).strip()

        url = str(
            item.get(
                "url",
                ""
            )
        ).strip()

        if not title:
            fail(
                f"La noticia {item['numero']} "
                "no tiene título."
            )

        if not summary:
            fail(
                f"La noticia {item['numero']} "
                "no tiene resumen."
            )

        if not category:
            fail(
                f"La noticia {item['numero']} "
                "no tiene categoría."
            )

        if not source:
            fail(
                f"La noticia {item['numero']} "
                "no tiene fuente."
            )

        if not url:
            fail(
                f"La noticia {item['numero']} "
                "no tiene URL."
            )

        title_highlights = item.get(
            "tituloDestacado"
        )

        summary_highlights = item.get(
            "resumenDestacado"
        )

        if not isinstance(
            title_highlights,
            list,
        ) or not (
            1 <= len(title_highlights) <= 2
        ):
            fail(
                f"La noticia {item['numero']} debe tener "
                "1 o 2 tituloDestacado."
            )

        if not isinstance(
            summary_highlights,
            list,
        ) or not (
            1 <= len(summary_highlights) <= 2
        ):
            fail(
                f"La noticia {item['numero']} debe tener "
                "1 o 2 resumenDestacado."
            )

        for fragment in title_highlights:
            fragment = str(
                fragment
            ).strip()

            if not fragment:
                fail(
                    f"La noticia {item['numero']} tiene "
                    "tituloDestacado vacío."
                )

            if fragment not in title:
                print(
                    f'⚠️ WARNING [{item["numero"]}]: '
                    f'el destacado {fragment!r} '
                    "no aparece literalmente en el título. "
                    "Se continuará sin bloquear el pipeline."
                )

        for fragment in summary_highlights:
            fragment = str(
                fragment
            ).strip()

            if not fragment:
                fail(
                    f"La noticia {item['numero']} tiene "
                    "resumenDestacado vacío."
                )

            if fragment not in summary:
                print(
                    f'⚠️ WARNING [{item["numero"]}]: '
                    f'el destacado {fragment!r} '
                    "no aparece literalmente en el resumen. "
                    "Se continuará sin bloquear el pipeline."
                )

        print(
            f'✅ {item["numero"]} '
            f'[{branch}] '
            f'{title[:74]}'
        )

    # La distribución válida es:
    # 2/2/2 o cualquier 3/2/1.
    for branch, count in branch_counts.items():
        if count < 1 or count > 3:
            fail(
                "Distribución editorial inválida: "
                f"{branch_counts}"
            )

    if sum(
        branch_counts.values()
    ) != EXPECTED_COUNT:
        fail(
            "La suma de ramas no coincide con "
            f"{EXPECTED_COUNT}."
        )

    print()
    print("Distribución:")
    print(
        "  Gaming:      "
        f'{branch_counts["gaming"]}'
    )
    print(
        "  Tecnología:  "
        f'{branch_counts["tecnologia"]}'
    )
    print(
        "  Cultura Pop: "
        f'{branch_counts["cultura_pop"]}'
    )

    print()
    print(
        "✅ VALIDACIÓN COMPLETADA"
    )
    print(
        f"✅ {EXPECTED_COUNT} noticias listas"
    )
    print()


if __name__ == "__main__":
    main()
