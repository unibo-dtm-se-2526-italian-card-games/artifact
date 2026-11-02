"""Architecture checks on the package imports (NFR-01).

The modules are read with `ast`, not imported, so the check is static and does not
depend on which frameworks happen to be installed.
"""

import ast
from pathlib import Path

import pytest

import italian_card_games

PACKAGE_ROOT = Path(italian_card_games.__file__).parent
FRAMEWORKS = {"fastapi", "nicegui", "sqlalchemy", "starlette", "pydantic"}
CORE = ("engine", "history", "lobby")
FORBIDDEN_INSIDE = {
    "engine": {"ai", "api", "cli", "history", "lobby", "persistence"},
    "history": {"ai", "api", "cli", "lobby", "persistence"},
    "lobby": {"ai", "api", "cli", "history", "persistence"},
}
# The composition root is the one module of api/ allowed to name an adapter.
COMPOSITION_ROOT = "api/main.py"


def imported_modules(package: str) -> dict[str, set[str]]:
    """Every absolute module each file of a subpackage imports, by file name."""
    found: dict[str, set[str]] = {}
    for path in sorted((PACKAGE_ROOT / package).rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.add(node.module)
        found[path.relative_to(PACKAGE_ROOT).as_posix()] = modules
    return found


class TestCoreIsFrameworkFree:
    @pytest.mark.parametrize("package", CORE)
    def test_nfr01_the_core_package_has_modules_to_check(self, package: str) -> None:
        assert imported_modules(package)

    @pytest.mark.parametrize("package", CORE)
    def test_nfr01_the_core_imports_no_framework(self, package: str) -> None:
        offending = {
            file: sorted(m for m in modules if m.split(".")[0] in FRAMEWORKS)
            for file, modules in imported_modules(package).items()
        }
        assert {file: m for file, m in offending.items() if m} == {}

    @pytest.mark.parametrize("package", CORE)
    def test_nfr01_the_core_depends_only_inwards(self, package: str) -> None:
        forbidden = {f"italian_card_games.{name}" for name in FORBIDDEN_INSIDE[package]}
        offending = {
            file: sorted(m for m in modules if ".".join(m.split(".")[:2]) in forbidden)
            for file, modules in imported_modules(package).items()
        }
        assert {file: m for file, m in offending.items() if m} == {}


class TestApiDependsOnPorts:
    """The API talks to ports; only the composition root may name an adapter."""

    def test_nfr01_the_api_package_has_modules_to_check(self) -> None:
        assert imported_modules("api")

    def test_nfr01_only_the_composition_root_imports_sqlalchemy(self) -> None:
        offending = {
            file: sorted(m for m in modules if m.split(".")[0] == "sqlalchemy")
            for file, modules in imported_modules("api").items()
            if file != COMPOSITION_ROOT
        }
        assert {file: m for file, m in offending.items() if m} == {}

    def test_nfr01_only_the_composition_root_imports_the_adapters(self) -> None:
        adapters = {"italian_card_games.persistence", "italian_card_games.ai"}
        offending = {
            file: sorted(m for m in modules if ".".join(m.split(".")[:2]) in adapters)
            for file, modules in imported_modules("api").items()
            if file != COMPOSITION_ROOT
        }
        assert {file: m for file, m in offending.items() if m} == {}

    def test_nfr01_the_api_does_not_import_the_cli(self) -> None:
        offending = {
            file: sorted(m for m in modules if m == "italian_card_games.cli")
            for file, modules in imported_modules("api").items()
        }
        assert {file: m for file, m in offending.items() if m} == {}
