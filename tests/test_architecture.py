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
CORE = ("engine", "history")
FORBIDDEN_INSIDE = {
    "engine": {"ai", "cli", "history", "persistence"},
    "history": {"ai", "cli", "persistence"},
}


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
