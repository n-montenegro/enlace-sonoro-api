"""test_mutation_score.py - El script del pipeline calcula bien el score y falla por debajo del mínimo."""
import json
import os
import subprocess
import sys

from scripts.mutation_score import mutation_score

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "mutation_score.py")


def test_score_counts_killed_and_timeouts_over_evaluated():
    assert mutation_score({"killed": 70, "timeout": 5, "total": 110, "skipped": 10}) == 75.0
    assert mutation_score({"killed": 0, "total": 0}) == 0.0


def run(tmp_path, stats, minimum):
    path = tmp_path / "stats.json"
    path.write_text(json.dumps(stats), encoding="utf-8")
    env = {**os.environ, "GITHUB_STEP_SUMMARY": ""}
    return subprocess.run([sys.executable, SCRIPT, "--min", str(minimum), "--stats", str(path)],
                          capture_output=True, text=True, env=env)


def test_build_fails_when_score_is_below_minimum(tmp_path):
    result = run(tmp_path, {"killed": 40, "survived": 60, "total": 100}, 50)
    assert result.returncode == 1
    assert "FAIL" in result.stdout


def test_build_passes_when_score_reaches_minimum(tmp_path):
    result = run(tmp_path, {"killed": 50, "survived": 50, "total": 100}, 50)
    assert result.returncode == 0
