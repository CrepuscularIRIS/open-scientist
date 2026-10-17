"""Broken package references must be caught before distribution."""
import importlib.util
from pathlib import Path

import pytest


def validator():
    path = Path(__file__).parents[1] / "scripts" / "validate_package.py"
    assert path.exists(), "Package validator is not implemented"
    spec = importlib.util.spec_from_file_location("validate_package", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_active_link_missing_target_is_reported_but_archive_is_not_instructions(tmp_path):
    (tmp_path / "skills" / "example").mkdir(parents=True)
    active = tmp_path / "skills" / "example" / "SKILL.md"
    active.write_text("[needed](../../references/missing.md)\n")
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "old.md").write_text("[old](removed.md)\n")
    errors = validator().check_links(tmp_path)
    assert len(errors) == 1
    assert "missing.md" in errors[0]
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "missing.md").write_text("Reference data\n")
    assert validator().check_links(tmp_path) == []


def test_package_rejects_external_file_escape_and_allows_web_and_fragment(tmp_path):
    (tmp_path / "README.md").write_text("[bad](../private.md)\n[web](https://example.org)\n[part](#part)\n")
    errors = validator().check_links(tmp_path)
    assert len(errors) == 1
    assert "outside" in errors[0]


def test_fenced_examples_do_not_become_package_dependencies(tmp_path):
    (tmp_path / "README.md").write_text("```md\n[example](/project/result.md)\n```\n")
    assert validator().check_links(tmp_path) == []
