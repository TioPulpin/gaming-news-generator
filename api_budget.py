import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
BUDGET_FILE = BASE_DIR / "budget.json"
USAGE_FILE = BASE_DIR / "data" / "api_usage.json"
LIMA = ZoneInfo("America/Lima")

PRICES = {
    "gpt-5.6-terra": {"input": 2.00, "cached_input": 0.20, "output": 12.00},
    "gpt-5.6-luna": {"input": 0.20, "cached_input": 0.02, "output": 1.20},
}

def current_month():
    return datetime.now(LIMA).strftime("%Y-%m")

def load_budget():
    if not BUDGET_FILE.exists():
        raise FileNotFoundError("No existe budget.json.")
    return json.loads(BUDGET_FILE.read_text(encoding="utf-8"))

def empty_usage():
    return {
        "month": current_month(),
        "spent_usd": 0.0,
        "calls": 0,
        "text_usd": 0.0,
        "image_usd": 0.0,
        "history": [],
    }

def save_usage(usage):
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(
        json.dumps(usage, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def load_usage():
    if not USAGE_FILE.exists():
        usage = empty_usage()
        save_usage(usage)
        return usage
    usage = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
    if usage.get("month") != current_month():
        usage = empty_usage()
        save_usage(usage)
    return usage

def calculate_text_cost(model, input_tokens, output_tokens, cached_tokens=0):
    if model not in PRICES:
        raise ValueError(f"Modelo sin precio configurado: {model}")
    p = PRICES[model]
    input_tokens = int(input_tokens)
    output_tokens = int(output_tokens)
    cached_tokens = int(cached_tokens)
    normal_input = max(input_tokens - cached_tokens, 0)
    return (
        normal_input / 1_000_000 * p["input"]
        + cached_tokens / 1_000_000 * p["cached_input"]
        + output_tokens / 1_000_000 * p["output"]
    )

def budget_status():
    budget = load_budget()
    usage = load_usage()
    spent = float(usage.get("spent_usd", 0.0))
    warning = float(budget["warning_usd"])
    critical = float(budget["critical_usd"])
    stop = float(budget["internal_stop_usd"])

    if spent >= stop:
        level = "STOP"
    elif spent >= critical:
        level = "CRITICO"
    elif spent >= warning:
        level = "ADVERTENCIA"
    else:
        level = "NORMAL"

    return {
        "level": level,
        "spent": spent,
        "stop": stop,
        "monthly_budget": float(budget["monthly_budget_usd"]),
        "remaining_to_stop": max(stop - spent, 0.0),
    }

def assert_budget_available():
    status = budget_status()
    if status["level"] == "STOP":
        raise RuntimeError(f"STOP interno alcanzado: ${status['spent']:.4f}.")
    return status

def assert_budget_for_call(
    model,
    estimated_input_tokens,
    max_output_tokens,
    safety_margin_usd=0.01,
):
    status = assert_budget_available()
    reserve = calculate_text_cost(
        model=model,
        input_tokens=estimated_input_tokens,
        output_tokens=max_output_tokens,
        cached_tokens=0,
    ) + float(safety_margin_usd)
    projected = status["spent"] + reserve

    if projected > status["stop"]:
        raise RuntimeError(
            "Llamada bloqueada por presupuesto. "
            f"Gastado: ${status['spent']:.4f}; "
            f"reserva: ${reserve:.4f}; "
            f"proyección: ${projected:.4f}; "
            f"STOP: ${status['stop']:.2f}."
        )

    return {
        **status,
        "estimated_max_call_cost": reserve,
        "projected_after_call": projected,
    }

def register_text_usage(
    model,
    input_tokens,
    output_tokens,
    cached_tokens=0,
    label="",
):
    cost = calculate_text_cost(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
    )
    usage = load_usage()
    usage["spent_usd"] = float(usage.get("spent_usd", 0.0)) + cost
    usage["text_usd"] = float(usage.get("text_usd", 0.0)) + cost
    usage["calls"] = int(usage.get("calls", 0)) + 1
    usage.setdefault("history", []).append({
        "timestamp": datetime.now(LIMA).isoformat(),
        "type": "text",
        "label": label,
        "model": model,
        "input_tokens": int(input_tokens),
        "cached_tokens": int(cached_tokens),
        "output_tokens": int(output_tokens),
        "estimated_cost_usd": cost,
    })
    save_usage(usage)
    return cost

if __name__ == "__main__":
    s = budget_status()
    print()
    print("=" * 60)
    print(" GAMING NEWS GENERATOR - PRESUPUESTO API V3")
    print("=" * 60)
    print()
    print(f"Mes: {current_month()}")
    print(f"Estado: {s['level']}")
    print(f"Gastado: ${s['spent']:.4f}")
    print(f"Límite interno: ${s['stop']:.2f}")
    print(f"Presupuesto mensual: ${s['monthly_budget']:.2f}")
    print(f"Disponible hasta STOP: ${s['remaining_to_stop']:.4f}")
    print()
