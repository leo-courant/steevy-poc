"""Tool package — auto-discovers every tool module so `@register` self-collects.

To add a new tool: drop a `*.py` file in this folder that defines a function
decorated with `@register` + `@tool` (see `rag_search.py`). Nothing else needs to
change — it is imported automatically here and returned by `get_tools()`.
"""

from __future__ import annotations

import importlib
import pkgutil

from agent.tools.registry import get_tools

# Internal modules that are not themselves tool definitions.
_NON_TOOL_MODULES = {"registry"}


def _discover() -> None:
    for module in pkgutil.iter_modules(__path__):
        if module.name not in _NON_TOOL_MODULES:
            importlib.import_module(f"{__name__}.{module.name}")


_discover()

__all__ = ["get_tools"]
