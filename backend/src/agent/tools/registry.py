"""A tiny tool registry.

Decorate any LangChain tool with `@register` to expose it to the agent. The agent
calls `get_tools()` to receive every registered tool. That's the whole mechanism.
"""

from __future__ import annotations

from langchain_core.tools import BaseTool

_REGISTRY: list[BaseTool] = []


def register(tool: BaseTool) -> BaseTool:
    """Add a tool to the registry (used as a decorator). Returns the tool."""
    _REGISTRY.append(tool)
    return tool


def get_tools() -> list[BaseTool]:
    """Return all registered tools."""
    return list(_REGISTRY)
