"""
test_deployment_files.py - Pruebas de los archivos de despliegue (Guía 8).

Revisan que nadie "rompa" sin darse cuenta las buenas prácticas del Dockerfile, del docker-compose
y del pipeline de 4 etapas (por ejemplo, volver a correr el contenedor como root).
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def instructions(dockerfile: str) -> list:
    """Líneas del Dockerfile sin comentarios, uniendo las que terminan en '\\'."""
    text = re.sub(r"\\\n\s*", " ", dockerfile)
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def test_dockerfile_is_multi_stage():
    lines = instructions(read("Dockerfile"))
    stages = [line for line in lines if line.startswith("FROM ")]
    assert len(stages) == 2
    assert stages[0].endswith("AS builder")
    assert all("-slim" in stage for stage in stages)            # imagen base pequeña
    assert "COPY --from=builder /opt/venv /opt/venv" in lines   # solo se copia el entorno virtual


def test_dockerfile_runs_as_non_root_user():
    lines = instructions(read("Dockerfile"))
    users = [line for line in lines if line.startswith("USER ")]
    assert users == ["USER appuser"]
    assert lines.index("USER appuser") > max(i for i, line in enumerate(lines) if line.startswith("RUN "))


def test_dockerfile_has_healthcheck_and_locked_dependencies():
    lines = instructions(read("Dockerfile"))
    assert any(line.startswith("HEALTHCHECK") and "/health" in line for line in lines)
    install = [line for line in lines if "pip install" in line]
    assert len(install) == 1
    assert "--require-hashes" in install[0] and "--only-binary :all:" in install[0]
    assert "requirements-prod.txt" in install[0]
    assert not any(line.startswith("COPY . ") for line in lines)  # nunca se copia todo el proyecto


def test_dockerignore_keeps_secrets_out_of_the_image():
    ignored = read(".dockerignore").splitlines()
    for pattern in (".env", "*.db", "venv/", ".git/", "tests/"):
        assert pattern in ignored


def test_production_dependencies_are_the_versions_tested_in_ci():
    def pins(name):
        return dict(re.findall(r"^([a-z0-9_.-]+)==(\S+) \\$", read(name), flags=re.MULTILINE))
    prod, ci = pins("requirements-prod.txt"), pins("requirements-lock.txt")
    assert "psycopg" in prod and "fastapi" in prod
    assert "pytest" not in prod and "mutmut" not in prod   # herramientas de pruebas fuera de producción
    for package, version in prod.items():
        assert ci.get(package) == version, package


def test_compose_runs_api_and_database_with_health_checks():
    compose = read("docker-compose.yml")
    assert re.search(r"^  db:\n", compose, flags=re.MULTILINE)
    assert re.search(r"^  api:\n", compose, flags=re.MULTILINE)
    assert compose.count("healthcheck:") == 2
    assert "condition: service_healthy" in compose
    assert "DATABASE_URL: postgresql://enlace:${POSTGRES_PASSWORD}@db:5432/enlace_sonoro" in compose
    assert "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?" in compose  # sin contraseñas escritas en el archivo


def job(name: str) -> str:
    """Texto de un job del pipeline (desde '  nombre:' hasta el siguiente job)."""
    jobs = read(".github/workflows/ci.yml").split("\njobs:\n")[1]
    return re.search(rf"^  {name}:\n(.*?)(?=^  [a-z]+:\n|\Z)", jobs, flags=re.MULTILINE | re.DOTALL).group(1)


def test_pipeline_has_four_stages_in_order():
    assert "needs: tests" in job("mutation")
    assert "needs: [tests, mutation]" in job("build")       # 1. TEST  -> 2. BUILD
    assert "needs: build" in job("push")                    # 2. BUILD -> 3. PUSH
    assert "needs: push" in job("deploy")                   # 3. PUSH  -> 4. DEPLOY
    assert "if: github.event_name == 'push' && github.ref == 'refs/heads/main'" in job("push")


def test_secrets_are_only_used_in_the_step_that_needs_them():
    push, deploy = job("push"), job("deploy")
    assert push.count("secrets.DOCKERHUB_TOKEN") == 1 and "password-stdin" in push
    assert deploy.count("secrets.RENDER_DEPLOY_HOOK_URL") == 1
