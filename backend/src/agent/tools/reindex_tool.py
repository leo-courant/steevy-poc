"""Tool to trigger the ingestion pipeline (same behavior as `make index`).

Provides `reindex_kb(opts_json: str)` that accepts an optional JSON object:
  {"background": true|false}

If `background` is true the ingestion runs in a background thread and the tool
returns immediately. Concurrent reindex requests are serialized.
"""

from __future__ import annotations

import json
import threading
from typing import Optional

from langchain_core.tools import tool

from agent.tools.registry import register

# Simple in-process guard to avoid concurrent ingestion runs
_lock = threading.Lock()
_is_running = False


def _run_ingest_sync() -> int:
    from rag.ingest import run_ingestion

    return run_ingestion()


def _background_worker():
    global _is_running
    try:
        _run_ingest_sync()
    finally:
        with _lock:
            _is_running = False


@register
@tool
def reindex_kb(opts_json: Optional[str] = None) -> str:
    """Trigger reindexing of the knowledge base.

    opts_json: optional JSON string. Supported key:
      - background (bool): if true, run ingestion in background and return

    Returns a human-friendly status string.
    """
    global _is_running
    opts = {}
    if opts_json:
        try:
            opts = json.loads(opts_json)
        except Exception as e:
            return f"Invalid JSON: {e}"

    background = bool(opts.get("background", False))

    with _lock:
        if _is_running:
            return "Reindex already in progress"
        _is_running = True

    if background:
        thread = threading.Thread(target=_background_worker, daemon=True)
        thread.start()
        return "Reindex started in background"

    try:
        count = _run_ingest_sync()
        return f"Reindex complete: upserted {count} chunks"
    except Exception as e:
        return f"Reindex failed: {e}"
    finally:
        with _lock:
            _is_running = False
