import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
NEWS_FILE = BASE_DIR / "data" / "noticias.json"

news = json.loads(
    NEWS_FILE.read_text(encoding="utf-8")
)

for item in news:
    item["imagen"] = "assets/project-helix.jpg"

NEWS_FILE.write_text(
    json.dumps(
        news,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print()
print("==============================================")
print(" IMÁGENES DE PRUEBA ASIGNADAS")
print("==============================================")
print()

for item in news:
    print(
        item.get("numero"),
        "->",
        item.get("imagen")
    )

print()