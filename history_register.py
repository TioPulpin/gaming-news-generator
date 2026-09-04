from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


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

KEEP_DAYS = 30


def lima_today() -> str:
    if ZoneInfo is not None:
        try:
            return datetime.now(
                ZoneInfo("America/Lima")
            ).strftime("%Y-%m-%d")
        except Exception:
            pass

    return datetime.now().strftime(
        "%Y-%m-%d"
    )


def normalize_text(text: str) -> str:
    text = str(text or "").lower()

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        ch
        for ch in text
        if not unicodedata.combining(ch)
    )

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text,
    )

    return text.strip("-")


def first_value(
    item: dict,
    *keys: str,
) -> str:
    for key in keys:
        value = item.get(key)

        if value:
            return str(value).strip()

    return ""


def load_json(
    path: Path,
    default,
):
    if not path.exists():
        return default

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return default


def parse_date(
    value: str,
) -> datetime | None:
    try:
        return datetime.fromisoformat(
            str(value)[:10]
        )
    except Exception:
        return None


def prune_history(
    history: list[dict],
) -> list[dict]:
    cutoff = (
        datetime.now()
        - timedelta(days=KEEP_DAYS)
    )

    result = []

    for item in history:
        date_value = parse_date(
            item.get("date", "")
        )

        if date_value is None:
            continue

        if date_value >= cutoff:
            result.append(item)

    return result


def main() -> None:
    print()
    print("=" * 64)
    print(
        " REGISTRO DE NOTICIAS PUBLICADAS "
    )
    print("=" * 64)
    print()

    news = load_json(
        NEWS_FILE,
        [],
    )

    if not isinstance(news, list):
        raise RuntimeError(
            "noticias.json no contiene una lista."
        )

    if not news:
        raise RuntimeError(
            "noticias.json está vacío."
        )

    history = load_json(
        HISTORY_FILE,
        [],
    )

    if not isinstance(history, list):
        history = []

    history = prune_history(
        history
    )

    today = lima_today()

    added = 0

    for index, item in enumerate(
        news,
        start=1,
    ):
        title = first_value(
            item,
            "titulo",
            "title",
            "headline",
        )

        if not title:
            print(
                f"Tarjeta {index}: "
                "sin título, omitida."
            )
            continue

        url = first_value(
            item,
            "url",
            "link",
            "enlace",
        )

        source = first_value(
            item,
            "fuente",
            "source",
        )

        category = first_value(
            item,
            "categoria",
            "category",
            "rama",
        )

        story_key = (
            normalize_text(title)[:140]
        )

        already_exists = any(
            old.get("date") == today
            and (
                old.get("url") == url
                if url
                else old.get(
                    "story_key"
                ) == story_key
            )
            for old in history
        )

        if already_exists:
            print(
                f"Ya registrada: {title}"
            )
            continue

        history.append(
            {
                "date": today,
                "branch": category,
                "title": title,
                "source": source,
                "url": url,
                "story_key": story_key,
            }
        )

        added += 1

        print(
            f"Registrada: {title}"
        )

    HISTORY_FILE.write_text(
        json.dumps(
            history,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        f"Nuevas registradas: {added}"
    )
    print(
        f"Entradas guardadas: "
        f"{len(history)}"
    )
    print()
    print(
        "✅ Historial actualizado."
    )


if __name__ == "__main__":
    main()