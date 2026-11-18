"""
mutation_score.py - Calcula el Mutation Score y hace FALLAR el pipeline si es menor al mínimo.

Lee mutants/mutmut-cicd-stats.json (lo genera "mutmut export-cicd-stats").
Score = mutantes detectados (killed + timeout) / mutantes evaluados (total - skipped) * 100

Uso:  python scripts/mutation_score.py --min 50
"""
import argparse
import json
import os
import sys

STATS_FILE = os.path.join("mutants", "mutmut-cicd-stats.json")


def mutation_score(stats: dict) -> float:
    detected = stats["killed"] + stats.get("timeout", 0)
    evaluated = stats["total"] - stats.get("skipped", 0)
    return round(detected * 100 / evaluated, 2) if evaluated else 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=float, default=50.0, help="score mínimo para que el build pase")
    parser.add_argument("--stats", default=STATS_FILE)
    args = parser.parse_args()

    with open(args.stats, encoding="utf-8") as f:
        stats = json.load(f)
    score = mutation_score(stats)
    passed = score >= args.min

    report = "\n".join([
        "## Mutation testing (mutmut)",
        "",
        "| Total | Killed | Survived | No tests | Timeout | Score | Minimum | Result |",
        "|---|---|---|---|---|---|---|---|",
        f"| {stats['total']} | {stats['killed']} | {stats['survived']} | {stats.get('no_tests', 0)} | "
        f"{stats.get('timeout', 0)} | **{score}%** | {args.min}% | {'PASS' if passed else 'FAIL'} |",
        "",
    ])
    print(report)
    summary = os.getenv("GITHUB_STEP_SUMMARY")  # en GitHub Actions se muestra en la página del run
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report)

    if not passed:
        print(f"Mutation score {score}% is below the minimum of {args.min}%: failing the build.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
