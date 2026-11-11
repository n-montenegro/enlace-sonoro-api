"""
test_architecture.py - Verifica las reglas de la arquitectura hexagonal leyendo los imports.

Regla de dependencias (siempre hacia ADENTRO):
  domain          -> no importa ninguna otra capa ni librerías externas
  application     -> solo importa domain
  infrastructure  -> importa domain (implementa sus puertos), nunca api ni application
  api             -> importa application y domain, nunca infrastructure
"""
import ast
import pathlib

APP = pathlib.Path(__file__).resolve().parents[2] / "app"
EXTERNAL = {"fastapi", "httpx", "duckdb", "sqlite3", "pydantic", "dotenv", "uvicorn"}


def imports_of(layer: str) -> set:
    found = set()
    for file in (APP / layer).rglob("*.py"):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module)
            elif isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
    return found


def uses(imports: set, prefix: str) -> bool:
    return any(m == prefix or m.startswith(prefix + ".") for m in imports)


def test_four_layers_exist():
    for layer in ("domain", "application", "api", "infrastructure"):
        assert (APP / layer).is_dir(), f"falta la capa {layer}"


def test_domain_has_no_external_dependencies():
    imports = imports_of("domain")
    for forbidden in ["app.application", "app.api", "app.infrastructure", *EXTERNAL]:
        assert not uses(imports, forbidden), f"domain no puede importar {forbidden}"


def test_application_only_depends_on_domain():
    imports = imports_of("application")
    for forbidden in ["app.api", "app.infrastructure", *EXTERNAL]:
        assert not uses(imports, forbidden), f"application no puede importar {forbidden}"


def test_infrastructure_does_not_depend_on_api_or_application():
    imports = imports_of("infrastructure")
    assert not uses(imports, "app.api")
    assert not uses(imports, "app.application")


def test_api_does_not_depend_on_infrastructure():
    assert not uses(imports_of("api"), "app.infrastructure")
