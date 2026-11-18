"""test_mutation_score.py - El script del pipeline calcula bien el score y falla por debajo del mínimo."""
import json
import sys

import pytest

from scripts import mutation_score as script


def test_score_counts_killed_and_timeouts_over_evaluated():
    assert script.mutation_score({"killed": 70, "timeout": 5, "total": 110, "skipped": 10}) == 75.0
    assert script.mutation_score({"killed": 0, "total": 0}) == 0.0


def run(tmp_path, monkeypatch, stats, *cli_args):
    """Ejecuta main() dentro de una carpeta temporal que tiene mutants/mutmut-cicd-stats.json."""
    (tmp_path / "mutants").mkdir()
    (tmp_path / "mutants" / "mutmut-cicd-stats.json").write_text(json.dumps(stats), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(sys, "argv", ["mutation_score.py", *cli_args])
    return script.main()


def test_build_fails_when_score_is_below_minimum(tmp_path, monkeypatch, capsys):
    assert run(tmp_path, monkeypatch, {"killed": 40, "survived": 60, "total": 100}, "--min", "50") == 1
    assert "FAIL" in capsys.readouterr().out


def test_build_passes_when_score_reaches_minimum(tmp_path, monkeypatch, capsys):
    assert run(tmp_path, monkeypatch, {"killed": 50, "survived": 50, "total": 100}, "--min", "50") == 0
    assert "PASS" in capsys.readouterr().out


def test_report_is_written_to_github_summary(tmp_path, monkeypatch):
    summary = tmp_path / "summary.md"
    (tmp_path / "mutants").mkdir()
    (tmp_path / "mutants" / "mutmut-cicd-stats.json").write_text(
        json.dumps({"killed": 9, "survived": 1, "total": 10}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setattr(sys, "argv", ["mutation_score.py"])
    assert script.main() == 0
    assert "**90.0%**" in summary.read_text(encoding="utf-8")


def test_stats_path_can_not_be_chosen_from_the_command_line(tmp_path, monkeypatch):
    """Regresión del Path Traversal reportado por SonarQube Cloud: la opción --stats ya no existe."""
    with pytest.raises(SystemExit) as exc:
        run(tmp_path, monkeypatch, {"killed": 1, "survived": 0, "total": 1}, "--stats", "../../etc/passwd")
    assert exc.value.code == 2  # argparse rechaza el argumento desconocido
