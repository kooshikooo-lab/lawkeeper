"""Self-tests for check_declared_dependencies.py (Law 13).

Real oracle: a genuinely-missing package name and a genuine
name-vs-import-name mismatch (pyyaml -> yaml), not just checking the
script's own opinion of itself.
"""

from conftest import load_script

check_declared_dependencies = load_script("check_declared_dependencies.py")


def test_detects_a_genuinely_missing_package():
    missing = check_declared_dependencies.check_group(
        ["this-package-definitely-does-not-exist-xyz>=1.0"], "test"
    )
    assert missing == ["this-package-definitely-does-not-exist-xyz>=1.0"]


def test_resolves_pypi_name_to_import_name_mismatch():
    """pyyaml is declared under that name on PyPI but imports as `yaml` --
    a naive check using the declared name literally would always report it
    missing even when installed."""
    missing = check_declared_dependencies.check_group(["pyyaml>=6.0"], "test")
    assert missing == []


def test_package_name_strips_version_specifiers():
    assert check_declared_dependencies._package_name("pytest>=7") == "pytest"
    assert check_declared_dependencies._package_name("pyyaml>=6.0,<7") == "pyyaml"
    assert check_declared_dependencies._package_name("requests[socks]") == "requests"


def test_real_dependencies_in_this_repo_all_import():
    """Sanity check against the actual pyproject.toml, not a fixture --
    this repo's own declared dependencies must genuinely import."""
    import tomllib

    data = tomllib.loads(check_declared_dependencies.PYPROJECT.read_text(encoding="utf-8"))
    required = data.get("project", {}).get("dependencies", [])
    assert required, "pyproject.toml should declare at least one dependency"
    missing = check_declared_dependencies.check_group(required, "dependencies")
    assert missing == [], f"real declared dependencies failed to import: {missing}"


def test_exit_code_reflects_missing_required_dependencies(monkeypatch, tmp_path):
    """End-to-end: a pyproject.toml with a fake required dependency must
    make main() return a nonzero exit code."""
    fake_pyproject = tmp_path / "pyproject.toml"
    fake_pyproject.write_text(
        '[project]\ndependencies = ["this-package-definitely-does-not-exist-xyz"]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(check_declared_dependencies, "PYPROJECT", fake_pyproject)
    assert check_declared_dependencies.main() == 1
