"""
cost_estimate.py - Estimación de costos del LLM a partir de las llamadas REALES registradas.

Ejecutar (después de run_experiments.py):
    py -3.14 scripts/cost_estimate.py

Lee logs/llm_calls.jsonl, calcula los tokens promedio por llamada y proyecta el costo mensual.
Genera docs/cost_estimate.md (en inglés, como pide la guía).

IMPORTANTE: verifica los precios en la página oficial antes de entregar
(https://ai.google.dev/gemini-api/docs/pricing) y cámbialos aquí si son distintos.
"""
import json
import os
from datetime import date

MODEL = "gemini-3.5-flash-lite"
PRICE_INPUT_PER_1M = 0.30    # USD por 1 millón de tokens de entrada (paid tier, standard)
PRICE_OUTPUT_PER_1M = 2.50   # USD por 1 millón de tokens de salida (incluye "thinking tokens")

# Escenarios de uso: (nombre, usuarios activos, consultas por usuario al día)
SCENARIOS = [
    ("Class pilot", 30, 3),
    ("University launch", 500, 5),
    ("City-wide growth", 5000, 5),
]
DAYS_PER_MONTH = 30


def load_successful_calls(path: str = os.path.join("logs", "llm_calls.jsonl")) -> list:
    if not os.path.exists(path):
        raise SystemExit(f"No existe {path}. Primero ejecuta scripts/run_experiments.py")
    with open(path, encoding="utf-8") as f:
        calls = [json.loads(line) for line in f if line.strip()]
    return [c for c in calls if c.get("status") == 200]


def main() -> None:
    calls = load_successful_calls()
    if not calls:
        raise SystemExit("No hay llamadas exitosas registradas.")

    n = len(calls)
    avg_in = sum(c["input_tokens"] for c in calls) / n
    avg_out = sum(c["output_tokens"] + c.get("thinking_tokens", 0) for c in calls) / n
    cost_per_call = avg_in / 1e6 * PRICE_INPUT_PER_1M + avg_out / 1e6 * PRICE_OUTPUT_PER_1M

    by_technique = {}
    for c in calls:
        t = by_technique.setdefault(c["technique"], {"n": 0, "in": 0, "out": 0})
        t["n"] += 1
        t["in"] += c["input_tokens"]
        t["out"] += c["output_tokens"] + c.get("thinking_tokens", 0)

    lines = [
        "# LLM cost estimate", "",
        f"Generated on {date.today().isoformat()} from **{n} real calls** logged in `logs/llm_calls.jsonl`.", "",
        "## Pricing used", "",
        f"- Model: `{MODEL}` (Gemini Developer API, paid tier, standard)",
        f"- Input: **${PRICE_INPUT_PER_1M:.2f}** per 1M tokens",
        f"- Output: **${PRICE_OUTPUT_PER_1M:.2f}** per 1M tokens (thinking tokens are billed as output)",
        "- Source: https://ai.google.dev/gemini-api/docs/pricing (checked on the generation date)", "",
        "## Average tokens per call", "",
        "| Technique | Calls | Avg input tokens | Avg output tokens |",
        "|---|---|---|---|",
    ]
    for name, t in by_technique.items():
        lines.append(f"| {name} | {t['n']} | {t['in'] / t['n']:.0f} | {t['out'] / t['n']:.0f} |")
    lines += [
        f"| **All** | {n} | {avg_in:.0f} | {avg_out:.0f} |", "",
        f"Average cost per call: **${cost_per_call:.6f}** USD", "",
        "## Monthly projection", "",
        "| Scenario | Active users | Requests/user/day | Requests/month | Estimated cost/month (USD) |",
        "|---|---|---|---|---|",
    ]
    for name, users, per_day in SCENARIOS:
        monthly = users * per_day * DAYS_PER_MONTH
        lines.append(f"| {name} | {users:,} | {per_day} | {monthly:,} | ${monthly * cost_per_call:,.2f} |")
    lines += [
        "", "## Notes", "",
        "- During development the project uses the **free tier**, so the real cost is $0; "
        "the free tier has request limits and Google may use the data to improve its products.",
        "- Few-shot and chain-of-thought prompts use more tokens than zero-shot (longer prompts and longer answers), "
        "so the chosen technique directly affects the bill.",
        "- Costs could be reduced by sending fewer catalog songs as context, limiting the answer length "
        "or using the Batch API for non-interactive tasks.", "",
    ]
    os.makedirs("docs", exist_ok=True)
    with open("docs/cost_estimate.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print("\nArchivo generado: docs/cost_estimate.md")


if __name__ == "__main__":
    main()
