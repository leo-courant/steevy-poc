# STEEVY-AI — Guide to the agent

Everything that defines the agent's behaviour lives in [backend/src/agent/](backend/src/agent/).
This is a quick map of what each piece does and how to change it.

## Folder layout

```
backend/src/agent/
├── AGENTS.md          # the agent's instructions / persona (loaded at runtime)
├── agent.py           # build_agent(): assembles instructions + skills + tools
├── skills/
│   └── search-knowledge-base/
│       └── SKILL.md   # one focused capability, described in plain language
└── tools/
    ├── registry.py    # @register decorator + get_tools()
    ├── __init__.py    # auto-discovers tool modules so they self-register
    └── rag_search.py  # the RAG retrieval tool (example tool)
```

[agent.py](backend/src/agent/agent.py) is the assembler. On startup `build_agent()`:
1. reads `AGENTS.md` as the system prompt,
2. appends every skill's `SKILL.md` underneath it,
3. collects every registered tool,
4. hands all three to `deepagents.create_deep_agent(...)`.

---

## AGENTS.md — the agent's instructions

[AGENTS.md](backend/src/agent/AGENTS.md) **is** the agent's operating manual: its persona,
its rules, and how it should behave. It is not documentation — its text is loaded verbatim
as the model's system prompt every time the agent is built.

**Modifying it** = changing how the agent thinks and answers. Edit the file in plain English:
tighten a rule ("always cite sources"), change the tone, add a new behaviour. No code change
is needed — the new text is picked up the next time a chat session starts. Keep it focused;
everything you write here is sent to the model on every request.

---

## Tools — what the agent can *do*

A tool is a Python function the agent can call. Adding one is two small steps.

**1. Write the tool** — drop a new file in [backend/src/agent/tools/](backend/src/agent/tools/),
e.g. `weather.py`:

```python
from langchain_core.tools import tool
from agent.tools.registry import register


@register
@tool
def get_weather(city: str) -> str:
    """Return the current weather for a city. The docstring is what the
    model reads to decide when to call this tool — make it clear."""
    return f"It is sunny in {city}."
```

**2. Hook it up** — there is no step 2. [tools/__init__.py](backend/src/agent/tools/__init__.py)
auto-imports every module in the folder, so the `@register` decorator adds your tool to the
registry automatically, and `build_agent()` already passes `get_tools()` to the agent. Restart
the app and the agent can use it.

How it wires together:
- `@tool` (LangChain) turns the function into a tool, generating its input schema from the
  type hints and its description from the docstring.
- `@register` ([tools/registry.py](backend/src/agent/tools/registry.py)) appends it to a list.
- `get_tools()` returns that list; `build_agent()` passes it to `create_deep_agent(tools=...)`.

[rag_search.py](backend/src/agent/tools/rag_search.py) is the worked example — it embeds the
query, searches Qdrant, and returns the matching chunks (with source + score) as a string. That
returned string is exactly what shows up in the expandable tool step in the UI.

> Tip: tool descriptions (the docstring) matter a lot. The model decides *whether* and *when*
> to call a tool from its description, so be explicit about when it applies.

---

## Skills — focused know-how the agent can draw on

A skill is a small Markdown file describing **one capability**: what it is, when to use it, and
how to use it well. Each skill lives in its own folder under
[skills/](backend/src/agent/skills/) as a `SKILL.md` (see
[search-knowledge-base/SKILL.md](backend/src/agent/skills/search-knowledge-base/SKILL.md)).

At startup, every `SKILL.md` is appended to the agent's instructions, so the agent is always
aware of the capabilities it has and the best way to apply them.

**Why skills matter:** tools give the agent *abilities*; skills give it *judgement*. A tool can
search the knowledge base, but a skill tells the agent things like "start with k=5, rephrase and
search again if the results are thin, cite the highest-scoring passages." Keeping that guidance
in a dedicated `SKILL.md` — rather than bloating `AGENTS.md` — keeps the core instructions short
and makes each capability easy to find, edit, and reason about on its own.

**Adding a skill:** create `skills/<your-skill>/SKILL.md` and write, in plain language, what the
capability is, when to reach for it, and how to do it well. It is loaded automatically — no code
change required.
