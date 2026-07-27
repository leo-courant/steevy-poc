"""A tiny tool registry.

Decorate any LangChain tool with `@register` to expose it to the agent. The agent
calls `get_tools()` to receive every registered tool. Groovy tools can also
declare required fields here so the wrapper can validate inputs before running.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Mapping, Sequence

from langchain_core.tools import BaseTool

_REGISTRY: list[BaseTool] = []


@dataclass(frozen=True)
class GroovyToolSpec:
    """Validation metadata for a Groovy-backed tool."""

    required_fields: tuple[str, ...]
    field_help: dict[str, str] = dataclass_field(default_factory=dict)
    default_values: dict[str, object] = dataclass_field(default_factory=dict)


_GROOVY_SPECS: dict[str, GroovyToolSpec] = {}


def register(tool: BaseTool) -> BaseTool:
    """Add a tool to the registry (used as a decorator). Returns the tool."""
    _REGISTRY.append(tool)
    return tool


def get_tools() -> list[BaseTool]:
    """Return all registered tools."""
    return list(_REGISTRY)


def register_groovy_spec(
    tool_name: str,
    *,
    required_fields: Sequence[str] = (),
    field_help: Mapping[str, str] | None = None,
    default_values: Mapping[str, object] | None = None,
) -> None:
    """Register required-field metadata for a Groovy tool."""
    _GROOVY_SPECS[tool_name] = GroovyToolSpec(
        required_fields=tuple(required_fields),
        field_help=dict(field_help or {}),
        default_values=dict(default_values or {}),
    )


def get_groovy_spec(tool_name: str) -> GroovyToolSpec | None:
    """Return the Groovy validation metadata for a tool, if any."""
    return _GROOVY_SPECS.get(tool_name)
