"""Date/time tool - returns the current local date and time."""

from __future__ import annotations

from datetime import datetime

from langchain_core.tools import tool

from agent.tools.registry import register


@register
@tool
def current_datetime() -> str:
	"""Return the current local date and time in ISO-8601 format."""
	now = datetime.now().astimezone()
	return now.isoformat(timespec="seconds")
