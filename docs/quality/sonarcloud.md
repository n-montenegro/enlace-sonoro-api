# SonarQube Cloud – Issues corregidos

**Línea base:** primer análisis automático del commit `83980bf` (antes de la Guía 7):
3 issues de seguridad (calificación C), 9 de confiabilidad (C), 0 de mantenibilidad (A).
Quality Gate: *Not computed* (primer análisis).

| # | Archivo | Issue de SonarQube Cloud | Tipo / severidad | Corrección | Prueba de regresión |
|---|---|---|---|---|---|
| 1–6 | `app/infrastructure/persistence/sqlite_song_repository.py` (L45–46) | *Make sure this object defines an `__index__` method* (6 issues, una por columna leída con `row["..."]`) | Reliability / Medium | La fila de SQLite se convierte en diccionario: `Song(**dict(row))`. Se aplicó lo mismo en `sqlite_user_repository.py` para no introducir el mismo bug | `test_song_row_is_mapped_to_entity_with_every_field`, `test_song_without_album_keeps_none`, `test_user_row_is_mapped_to_entity` |
| 7–9 | `app/api/static/dashboard.html` (L41, L48, L53) | *Add `<th>` headers to this `<table>`* (accesibilidad WCAG 2) | Reliability / Medium | Cada tabla tiene `<thead>` con `<th scope="col">`; el JavaScript ahora llena el `<tbody>` | `test_dashboard_tables_have_header_cells` |
| 10 | `.github/workflows/ci.yml` (L22) | *Omitting `--only-binary :all:` can lead to the execution of setup scripts* | Security / Medium | `pip install --only-binary :all: ...` (solo paquetes binarios, no se ejecuta `setup.py`) | `test_ci_installs_locked_binary_dependencies` |
| 11 | `.github/workflows/ci.yml` (L22) | *Using dependencies without locking resolved versions is security-sensitive* | Security / Medium | Nuevo `requirements-lock.txt` generado con `pip-compile --generate-hashes`: todas las dependencias (también las indirectas) con versión fija y hash SHA-256; el CI usa `--require-hashes` | `test_ci_installs_locked_binary_dependencies` |
| extra | `.github/workflows/ci.yml` | Acciones de GitHub referenciadas por etiqueta (`@v4`), que su autor puede mover | Security (prevención) | Acciones fijadas por SHA completo, con la versión en un comentario | `test_ci_actions_are_pinned_to_a_full_commit_sha` |

| 12 | `scripts/mutation_score.py` (L29) | *Path Traversal via faulty CLI arguments* (CWE-22): la ruta del archivo `--stats` se abría sin validar. Apareció en el análisis del pipeline después de subir la Guía 7 (Quality Gate: Failed, Security Rating C) | Security / High | Se eliminó la opción `--stats`; el script siempre lee `mutants/mutmut-cicd-stats.json` | `test_stats_path_can_not_be_chosen_from_the_command_line` (en `tests/unit/test_mutation_score.py`) |

Las pruebas de regresión están en `tests/integration/test_sonar_regressions.py`.

## Configuración del análisis desde el pipeline

- `sonar-project.properties`: proyecto, organización y reporte de cobertura (`coverage.xml`).
  Se quitaron `sonar.sources` y `sonar.tests` porque el nuevo modo de análisis los ignora (advertencia del análisis).
- El job `tests` de `.github/workflows/ci.yml` genera la cobertura con `pytest-cov` y ejecuta
  `SonarSource/sonarqube-scan-action` usando el secreto `SONAR_TOKEN`.
- En SonarQube Cloud se desactiva el *Automatic Analysis* (Administration → Analysis Method),
  porque el análisis ahora lo hace el pipeline e incluye la cobertura.
