"""Wrappers to call Groovy XML tools from the Python agent.

Expose every Groovy script as LangChain tools and register them so the
agent can call them like other tools. The tools accept a JSON string with
options (key/value) which are converted to CLI args for the Groovy scripts.
"""
from __future__ import annotations

import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Dict

from langchain_core.tools import tool

# from agent.tools.registry import register
# from agent.tools.reindex_tool import reindex_kb


class MissingGroovyFieldsError(ValueError):
    """Raised when a Groovy tool is called without required inputs."""

    def __init__(
        self,
        tool_name: str,
        missing_fields: tuple[str, ...],
        options: Dict[str, object],
    ) -> None:
        self.tool_name = tool_name
        self.missing_fields = missing_fields
        # Keep a copy because the caller's dictionary may be reused or modified.
        self.options = dict(options)
        super().__init__(_missing_fields_message(tool_name, missing_fields))


_GROOVY_DEFAULT_VALUES: dict[str, object] = {
    'xml': 'data/rag/sample.xml',
}
_REQUIRED_GROOVY_OPTION_RE = re.compile(
    r"^\s*\w+\s+longOpt:\s*['\"](?P<option>[^'\"]+)['\"][^\n]*required:\s*true\b",
    re.MULTILINE,
)

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]
print(_repo_root())

@lru_cache(maxsize=None)
def _required_groovy_fields(script_path: str) -> tuple[str, ...]:
    script_file = _repo_root() / script_path
    text = script_file.read_text(encoding='utf-8')
    return tuple(match.group('option') for match in _REQUIRED_GROOVY_OPTION_RE.finditer(text))


def _is_missing_value(value: object) -> bool:
    """définit ce que "champ manquant" signifie."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == '':
        return True
    return False


def _missing_fields_message(tool_name: str, missing_fields: tuple[str, ...]) -> str:
    """construit le message d'erreur."""
    details = '\n'.join(f'- {field_name}' for field_name in missing_fields)
    return (
        f"Groovy tool '{tool_name}' is missing required field(s): "
        f"{', '.join(missing_fields)}. Ask the user for these values, then retry.\n"
        f"{details}"
    )


def _apply_groovy_defaults(opts: Dict[str, object]) -> None:
    """injecte les valeurs par défaut."""
    for field_name, default_value in _GROOVY_DEFAULT_VALUES.items():
        if _is_missing_value(opts.get(field_name)):
            opts[field_name] = default_value


def _validate_groovy_opts(tool_name: str, script_path: str, opts: Dict[str, object]) -> None:
    """compare les options reçues avec les champs required: true du script Groovy et lève MissingGroovyFieldsError si nécessaire."""
    missing_fields = [
        field_name
        for field_name in _required_groovy_fields(script_path)
        if _is_missing_value(opts.get(field_name))
    ]
    if missing_fields:
        raise MissingGroovyFieldsError(tool_name, tuple(missing_fields), opts)


def _call_groovy(tool_name: str, script_path: str, opts: Dict[str, object]) -> str:
    _apply_groovy_defaults(opts)
    _validate_groovy_opts(tool_name, script_path, opts)

    script_file = _repo_root() / script_path

    # Build CLI args from opts dict (skip None/False)
    args = ['groovy', str(script_file)]
    for k, v in opts.items():
        if v is None or v is False:
            continue
        flag = f'--{k}'
        args.append(flag)
        # Booleans would be handled above; convert others to string
        if not isinstance(v, bool):
            args.append(str(v))

    try:
        res = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(_repo_root()),
        )
    except FileNotFoundError as e:
        raise RuntimeError('groovy executable not found; install Groovy') from e

    if res.returncode != 0:
        # include stderr for diagnostics
        raise RuntimeError(f'Groovy script failed: {res.stderr.strip()}')

    return res.stdout.strip()


# @register
# @tool
# def add_boat(opts_json: str) -> str:
#     """Add a boat using the Groovy addBoat.groovy script.

#     `opts_json` must be a JSON object (string) with the same option names used
#     by the Groovy script (for example: {"xml":"data/rag/sample.xml","id":"B210","name":"MyBoat"}).
#     Returns the Groovy stdout on success.
#     """
#     opts = json.loads(opts_json)
#     out = _call_groovy('add_boat', 'backend/src/agent/tools/addBoat.groovy', opts)

#     # Trigger background reindex to keep KB in sync
#     try:
#         status = reindex_kb('{"background": true}')
#         out = out + f"\n{status}"
#     except Exception as e:
#         out = out + f"\nWarning: failed to trigger reindex: {e}"

#     return out


# @register
# @tool
# def update_boat(opts_json: str) -> str:
#     """Update a boat using the Groovy updateBoat.groovy script.

#     `opts_json` must be a JSON object (string) with `id` and any optional
#     fields to update (same option names as the Groovy script). Example:
#     '{"xml":"data/rag/sample.xml","id":"B209","ownerFirst":"Nicky"}'.
#     Returns the Groovy stdout on success.
#     """
#     opts = json.loads(opts_json)
#     out = _call_groovy('update_boat', 'backend/src/agent/tools/updateBoat.groovy', opts)

#     # Trigger background reindex to keep KB in sync
#     try:
#         status = reindex_kb('{"background": true}')
#         out = out + f"\n{status}"
#     except Exception as e:
#         out = out + f"\nWarning: failed to trigger reindex: {e}"

#     return out


# @register
# @tool
# def delete_boat(opts_json: str) -> str:
#     """Delete a boat using the Groovy deleteBoat.groovy script.

#     `opts_json` must be a JSON object (string) containing the boat `id` to
#     delete. `name` is optional; when provided, it must match the boat's name
#     as well as its id or no boat is deleted. The default XML file is used when
#     `xml` is omitted. Example:
#     '{"xml":"data/rag/sample.xml","id":"B209","name":"Sea Star"}'.
#     Returns the Groovy stdout on success.
#     """
#     opts = json.loads(opts_json)
#     out = _call_groovy('delete_boat', 'backend/src/agent/tools/deleteBoat.groovy', opts)

#     # Trigger background reindex to keep KB in sync.
#     try:
#         status = reindex_kb('{"background": true}')
#         out = out + f"\n{status}"
#     except Exception as e:
#         out = out + f"\nWarning: failed to trigger reindex: {e}"

#     return out

if __name__ == "__main__":
    script_path = r"backend\src\agent\tools\updateBoat.groovy"

    print("=" * 80)
    print("TEST _required_groovy_fields")
    print("=" * 80)
    print(f"Script : {script_path}")
    print()

    fields = _required_groovy_fields(script_path)

    print(f"Nombre de champs obligatoires : {len(fields)}")
    print()

    for i, field in enumerate(fields, start=1):
        print(f"{i}. {field}")

    print()
    print("Tuple retourné :")
    print(fields)