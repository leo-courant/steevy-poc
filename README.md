# steevy-poc

A proof-of-concept **RAG-over-XML deep agent** with a **Chainlit** chat frontend.

A LangGraph deep agent (via [`deepagents`](https://pypi.org/project/deepagents/)) answers
questions over a knowledge base built from XML files. The XML is parsed, chunked, embedded
with a local FastEmbed model, and stored in **Qdrant**. Retrieval is an agent tool, and
every tool call — including the RAG retrieval — shows up in the UI as an expandable step
with its inputs, the retrieved chunks (text + source metadata + similarity score), and the
agent's answer.

## Architecture

| Layer | Location | Responsibility |
| --- | --- | --- |
| Config | `backend/src/config/` | Typed, env-driven settings (pydantic-settings) |
| RAG | `backend/src/rag/` | XML parsing, chunking, embeddings, Qdrant store, ingestion |
| Agent | `backend/src/agent/` | `AGENTS.md` instructions, `skills/`, `tools/` registry |
| Frontend | `frontend/` | Chainlit app; streams agent events into the UI |
| Data | `data/rag/` | Drop-zone for `.xml` files (data only, no code) |

- **Add a tool:** drop a `*.py` file in `backend/src/agent/tools/` with a function decorated
  `@register` + `@tool`. It is auto-discovered — nothing else changes.
- **Add a skill:** add `backend/src/agent/skills/<name>/SKILL.md`. It is loaded into the
  agent's instructions at startup.
- **Add data:** drop `.xml` files in `data/rag/` and re-run `make index`.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) (dependency & environment management)
- Docker (for Qdrant)
- An OpenAI API key (the agent LLM)

## Quickstart (clone → running)

```bash
make init                       # uv sync + create .env from .env.example
# edit .env and set OPENAI_API_KEY=...

make qdrant-up                  # start Qdrant (dashboard: http://localhost:6333/dashboard)

# drop your .xml files into data/rag/ (a sample.xml is included)
make index                      # parse → chunk → embed → upsert into Qdrant

make run                        # start the Chainlit app on http://localhost:8000
```

Open the app, ask a question about your XML, and expand the `search_knowledge_base` step to
see exactly which chunks were retrieved.

## Make targets

```
make help            # list targets
make init            # install deps and create .env
make qdrant-up       # start Qdrant
make qdrant-down     # stop Qdrant
make qdrant-restart  # restart Qdrant
make index           # ingest data/rag/*.xml into Qdrant
make run             # start the Chainlit app
```

All Python runs through `uv run`; there is no venv to activate manually.

## Qdrant dashboard

`http://localhost:6333/dashboard` — inspect the `xml_knowledge_base` collection and its points.
