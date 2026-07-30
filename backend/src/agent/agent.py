"""Assemble the deep agent at runtime.

`build_agent()` loads the operating instructions from `AGENTS.md`, appends a
summary of the available skills (`skills/*/SKILL.md`), collects the registered
tools, and hands them to `deepagents.create_deep_agent`.
"""

from __future__ import annotations

from pathlib import Path

from deepagents import create_deep_agent

from agent.thales_integration import (
    build_thales_chat_model,
    configure_thales_environment,
)
from agent.tools import get_tools
from config import settings

_AGENT_DIR = Path(__file__).parent


def _load_skills() -> str:
    """Concatenate every skill's SKILL.md so the agent knows its capabilities."""
    blocks = [
        skill_md.read_text(encoding="utf-8").strip()
        for skill_md in sorted(_AGENT_DIR.glob("skills/*/SKILL.md"))
    ]
    return "\n\n".join(blocks)


def _load_instructions() -> str:
    """AGENTS.md is the agent's instructions; skills are appended underneath."""
    instructions = (_AGENT_DIR / "AGENTS.md").read_text(encoding="utf-8").strip()
    skills = _load_skills()
    if skills:
        instructions += "\n\n# Available skills\n\n" + skills
    return instructions


def build_agent():
    """Build and return the compiled LangGraph deep agent."""
    configure_thales_environment(settings)
    # The Thales gateway only implements /chat/completions, and deepagents
    # forces the /responses endpoint for string models — so hand it a
    # pre-configured ChatOpenAI instance instead of `settings.agent_model`.
    if settings.thales_base_url:
        model = build_thales_chat_model(settings) # THALES_BASE_URL needs to be filled
    else:
        model = settings.agent_model
    return create_deep_agent(
        model=model,
        tools=get_tools(),
        system_prompt=_load_instructions(),
    )
