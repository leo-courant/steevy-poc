from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from agent.tools.groovy_tools import (
    MissingGroovyFieldsError,
    _apply_groovy_defaults,
    _required_groovy_fields,
    _validate_groovy_opts,
)
from frontend.app import (
    _tool_error_message,
    _is_abandonment,
    _missing_fields_question,
    _pending_operation,
    _resume_prompt,
)


ADD_BOAT_SCRIPT = "backend/src/agent/tools/addBoat.groovy"
DELETE_BOAT_SCRIPT = "backend/src/agent/tools/deleteBoat.groovy"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _run_delete_boat(xml_file: Path, *options: str) -> subprocess.CompletedProcess[str]:
    """Run deleteBoat.groovy against an isolated XML test file."""
    groovy = shutil.which("groovy")
    if groovy is None:
        pytest.skip("Groovy is required to run deleteBoat.groovy integration tests")
    return subprocess.run(
        [groovy, str(REPOSITORY_ROOT / DELETE_BOAT_SCRIPT), "--xml", str(xml_file), *options],
        capture_output=True,
        check=False,
        text=True,
        cwd=REPOSITORY_ROOT,
    )


def test_required_fields_are_discovered_from_groovy_script() -> None:
    assert _required_groovy_fields(ADD_BOAT_SCRIPT) == ("xml", "id", "name")


def test_delete_boat_required_fields_are_discovered_from_groovy_script() -> None:
    assert _required_groovy_fields(DELETE_BOAT_SCRIPT) == ("xml", "id")


def test_delete_boat_allows_an_optional_matching_name(tmp_path: Path) -> None:
    xml_file = tmp_path / "boats.xml"
    shutil.copy(REPOSITORY_ROOT / "data/rag/sample.xml", xml_file)

    result = _run_delete_boat(xml_file, "--id", "B201X", "--name", "Northstar Voyager")

    assert result.returncode == 0, result.stderr
    assert 'id="B201X"' not in xml_file.read_text(encoding="utf-8")


def test_delete_boat_allows_omitting_the_name(tmp_path: Path) -> None:
    xml_file = tmp_path / "boats.xml"
    shutil.copy(REPOSITORY_ROOT / "data/rag/sample.xml", xml_file)

    result = _run_delete_boat(xml_file, "--id", "B202")

    assert result.returncode == 0, result.stderr
    assert 'id="B202"' not in xml_file.read_text(encoding="utf-8")


def test_delete_boat_rejects_a_name_that_does_not_match_the_id(tmp_path: Path) -> None:
    xml_file = tmp_path / "boats.xml"
    shutil.copy(REPOSITORY_ROOT / "data/rag/sample.xml", xml_file)
    original_xml = xml_file.read_text(encoding="utf-8")

    result = _run_delete_boat(xml_file, "--id", "B201X", "--name", "Wrong name")

    assert result.returncode == 4
    assert "and name Wrong name not found" in result.stderr
    assert xml_file.read_text(encoding="utf-8") == original_xml


def test_default_xml_is_added_before_validation() -> None:
    options: dict[str, object] = {"id": "B210", "name": "Aurora"}

    _apply_groovy_defaults(options)

    assert options["xml"] == "data/rag/sample.xml"
    _validate_groovy_opts("add_boat", ADD_BOAT_SCRIPT, options)


def test_missing_fields_error_contains_tool_fields_and_partial_options() -> None:
    options: dict[str, object] = {"id": "B210"}
    _apply_groovy_defaults(options)

    with pytest.raises(MissingGroovyFieldsError) as caught:
        _validate_groovy_opts("add_boat", ADD_BOAT_SCRIPT, options)

    error = caught.value
    assert error.tool_name == "add_boat"
    assert error.missing_fields == ("name",)
    assert error.options == {"id": "B210", "xml": "data/rag/sample.xml"}


def test_missing_tool_error_becomes_a_resumable_user_question() -> None:
    error = MissingGroovyFieldsError(
        "add_boat",
        ("id", "name"),
        {"xml": "data/rag/sample.xml"},
    )

    operation = _pending_operation("add_boat", error, {"opts_json": "{}"})

    assert operation == {
        "tool_name": "add_boat",
        "missing_fields": ["id", "name"],
        "options": {"xml": "data/rag/sample.xml"},
    }
    assert _missing_fields_question(operation) == (
        "Il me manque les informations suivantes pour ajouter le bateau : "
        "`id`, `name`. Pouvez-vous me les fournir ?"
    )


def test_missing_delete_identifier_becomes_a_delete_question() -> None:
    operation = {
        "tool_name": "delete_boat",
        "missing_fields": ["id"],
        "options": {"xml": "data/rag/sample.xml"},
    }

    assert _missing_fields_question(operation) == (
        "Il me manque les informations suivantes pour supprimer le bateau : "
        "`id`. Pouvez-vous me les fournir ?"
    )


def test_resume_prompt_preserves_action_and_partial_options() -> None:
    operation = {
        "tool_name": "add_boat",
        "missing_fields": ["name"],
        "options": {"id": "B210", "xml": "data/rag/sample.xml"},
    }

    prompt = _resume_prompt(operation, "Aurora")

    assert "add_boat" in prompt
    assert json.dumps(operation["options"], ensure_ascii=False) in prompt
    assert "Aurora" in prompt
    assert "uniquement les valeurs explicitement fournies" in prompt
    assert "n'invente" in prompt
    assert "n'appelle pas l'outil" in prompt


def test_unrelated_tool_error_shows_a_bounded_technical_detail() -> None:
    assert _pending_operation("add_boat", RuntimeError("connexion refusée"), {}) is None

    message = _tool_error_message(RuntimeError("connexion refusée"))
    assert "L’opération n’a pas abouti" in message
    assert "RuntimeError: connexion refusée" in message
    # Only the exception summary is shown — never a full traceback,
    # and long messages are truncated.
    assert "Traceback (most recent call last)" not in message
    long_message = _tool_error_message(RuntimeError("x" * 1000))
    assert len(long_message) < 600


def test_explicit_abandonment_clears_the_pending_operation() -> None:
    assert _is_abandonment("Annuler")
    assert _is_abandonment("cancel")
    assert not _is_abandonment("Le nom est Aurora")
