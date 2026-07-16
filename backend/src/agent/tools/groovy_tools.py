"""Wrappers to call Groovy XML tools from the Python agent.

Expose `add_boat` and `update_boat` as LangChain tools and register them so the
agent can call them like other tools. Both tools accept a JSON string with
options (key/value) which are converted to CLI args for the Groovy scripts.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from typing import Dict

from langchain_core.tools import tool

from agent.tools.registry import register
from agent.tools.reindex_tool import reindex_kb


def _call_groovy(script_path: str, opts: Dict[str, object]) -> str:
    # Build CLI args from opts dict (skip None/False)
    args = ['groovy', script_path]
    for k, v in opts.items():
        if v is None or v is False:
            continue
        flag = f'--{k}'
        args.append(flag)
        # Booleans would be handled above; convert others to string
        if not isinstance(v, bool):
            args.append(str(v))

    try:
        res = subprocess.run(args, capture_output=True, text=True, check=False)
    except FileNotFoundError as e:
        raise RuntimeError('groovy executable not found; install Groovy') from e

    if res.returncode != 0:
        # include stderr for diagnostics
        raise RuntimeError(f'Groovy script failed: {res.stderr.strip()}')

    return res.stdout.strip()


@register
@tool
def add_boat(opts_json: str) -> str:
    """Add a boat using the Groovy addBoat.groovy script.

    `opts_json` must be a JSON object (string) with the same option names used
    by the Groovy script (for example: {"xml":"data/rag/sample.xml","id":"B210","name":"MyBoat"}).
    Returns the Groovy stdout on success.
    """
    opts = json.loads(opts_json)
    out = _call_groovy('backend/src/agent/tools/addBoat.groovy', opts)

    # Trigger background reindex to keep KB in sync
    try:
        status = reindex_kb('{"background": true}')
        out = out + f"\n{status}"
    except Exception as e:
        out = out + f"\nWarning: failed to trigger reindex: {e}"

    return out


@register
@tool
def update_boat(opts_json: str) -> str:
    """Update a boat using the Groovy updateBoat.groovy script.

    `opts_json` must be a JSON object (string) with `id` and any optional
    fields to update (same option names as the Groovy script). Example:
    '{"xml":"data/rag/sample.xml","id":"B209","ownerFirst":"Nicky"}'.
    Returns the Groovy stdout on success.
    """
    opts = json.loads(opts_json)
    out = _call_groovy('backend/src/agent/tools/updateBoat.groovy', opts)

    # Trigger background reindex to keep KB in sync
    try:
        status = reindex_kb('{"background": true}')
        out = out + f"\n{status}"
    except Exception as e:
        out = out + f"\nWarning: failed to trigger reindex: {e}"

    return out
