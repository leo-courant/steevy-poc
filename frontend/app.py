"""Chainlit frontend.

Runs the backend deep agent in-process and bridges its LangGraph event stream
into the Chainlit UI:

  * every tool call becomes an expandable `cl.Step` showing its input and output
    (for `search_knowledge_base`, the output lists the retrieved chunks with their
    source metadata and similarity score);
  * the assistant's answer streams token-by-token into the chat message.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping

import chainlit as cl

from agent.agent import build_agent
from agent.tools.groovy_tools import MissingGroovyFieldsError


_MISSING_FIELDS_RE = re.compile(r"missing required field\(s\):\s*([^\.]+)", re.IGNORECASE)


@cl.on_chat_start
async def on_chat_start() -> None:
    # Build the agent once per chat session.
    cl.user_session.set("agent", build_agent())
    cl.user_session.set("history", [])
    cl.user_session.set("pending_operation", None)
    await cl.Message(
        content=(
            "### 👋 Hi! Welcome to **Steevy's POC**\n\n"
            "Ask a question about the documents in the knowledge base — I'll "
            "search them and answer with sources.\n\n"
            "_Tip: expand the **tool step** above any answer to see the exact "
            "chunks I retrieved (with their source and similarity score)._"
        )
    ).send()

@cl.on_message
async def on_message(message: cl.Message) -> None:
    agent = cl.user_session.get("agent")
    history = list(cl.user_session.get("history") or [])
    pending_operation = cl.user_session.get("pending_operation")
    history.append({"role": "user", "content": message.content})
    if pending_operation is not None and _is_abandonment(message.content):
        cl.user_session.set("history", history)
        cl.user_session.set("pending_operation", None)
        await cl.Message(content="Opération annulée.").send()
        return

    agent_messages = list(history)
    if pending_operation is not None:
        agent_messages[-1] = {
            "role": "user",
            "content": _resume_prompt(pending_operation, message.content),
        }

    # The agent may stream some assistant text *before* it decides to call a tool.
    # We only want the FINAL answer (streamed after the last tool call) to remain,
    # so it renders below the tool steps. Any text streamed before a tool starts is
    # discarded when that tool begins.
    answer: cl.Message | None = None
    open_steps: dict[str, cl.Step] = {}
    handled_error = False
    try:
        async for event in agent.astream_events(
            {"messages": agent_messages},
            version="v2",
        ):
            kind = event["event"]

            if kind == "on_tool_start":
                if answer is not None:
                    await answer.remove()
                    answer = None
                step = cl.Step(name=event["name"], type="tool")
                step.input = event["data"].get("input")
                await step.send()
                open_steps[event["run_id"]] = step

            elif kind == "on_tool_end":
                step = open_steps.pop(event["run_id"], None)
                if step is not None:
                    step.output = _as_text(event["data"].get("output"))
                    await step.update()

            elif kind == "on_tool_error":
                handled_error = True
                error = event["data"].get("error")
                step = open_steps.pop(event["run_id"], None)
                pending_operation = _pending_operation(event["name"], error, step.input if step else None)
                if pending_operation is not None:
                    if step is not None:
                        step.output = "Informations complémentaires requises."
                        await step.update()
                    await cl.Message(content=_missing_fields_question(pending_operation)).send()
                    cl.user_session.set("pending_operation", pending_operation)
                else:
                    if step is not None:
                        step.output = "Échec de l'opération."
                        await step.update()
                    await cl.Message(content=_generic_tool_error_message()).send()
                    cl.user_session.set("pending_operation", None)

            elif kind == "on_chat_model_stream":
                token = _as_text(event["data"].get("chunk"))
                if token:
                    if answer is None:
                        answer = cl.Message(content="")
                    await answer.stream_token(token)
    except Exception:
        if not handled_error:
            for step in open_steps.values():
                step.output = "Échec de l'opération."
                await step.update()
            await cl.Message(content=_generic_tool_error_message()).send()
            cl.user_session.set("pending_operation", None)
        handled_error = True

    if answer is not None and not handled_error:
        await answer.send()
        history.append({"role": "assistant", "content": answer.content})

    cl.user_session.set("history", history)
    if pending_operation is not None and not handled_error:
        cl.user_session.set("pending_operation", None)


def _as_text(value) -> str:
    """Coerce a LangChain message/chunk/tool output into display text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value

    content = getattr(value, "content", value)
    if isinstance(content, str):
        return content

    # Some providers stream content as a list of typed blocks rather than a str.
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(getattr(block, "text", "") or "")
        return "".join(parts)

    return str(content)


def _pending_operation(tool_name: str, error: object, tool_input: object) -> dict[str, object] | None:
    """Build resumable state from a structured Groovy validation error."""
    options = _options_from_tool_input(tool_input)
    if isinstance(error, MissingGroovyFieldsError):
        return {
            "tool_name": error.tool_name,
            "missing_fields": list(error.missing_fields),
            "options": error.options,
        }

    match = _MISSING_FIELDS_RE.search(str(error))
    if match is None:
        return None
    fields = [field.strip() for field in match.group(1).split(",") if field.strip()]
    if not fields:
        return None
    return {"tool_name": tool_name, "missing_fields": fields, "options": options}


def _options_from_tool_input(tool_input: object) -> dict[str, object]:
    if not isinstance(tool_input, Mapping):
        return {}
    opts_json = tool_input.get("opts_json")
    if not isinstance(opts_json, str):
        return {}
    try:
        options = json.loads(opts_json)
    except json.JSONDecodeError:
        return {}
    return options if isinstance(options, dict) else {}


def _missing_fields_question(operation: Mapping[str, object]) -> str:
    fields = ", ".join(f"`{field}`" for field in operation["missing_fields"])
    actions = {
        "add_boat": "ajouter",
        "update_boat": "mettre à jour",
        "delete_boat": "supprimer",
    }
    action = actions.get(operation["tool_name"], "effectuer une opération sur")
    return f"Il me manque les informations suivantes pour {action} le bateau : {fields}. Pouvez-vous me les fournir ?"


def _resume_prompt(operation: Mapping[str, object], reply: str) -> str:
    """Tell the agent to merge the answer into its interrupted tool call."""
    return (
        "Reprends l'opération interrompue sans demander à nouveau les informations déjà connues. "
        f"Outil à appeler : {operation['tool_name']}. "
        f"Options déjà reçues : {json.dumps(operation['options'], ensure_ascii=False)}. "
        f"Champs demandés : {', '.join(operation['missing_fields'])}. "
        f"Nouvelle réponse de l'utilisateur : {reply}. "
        "Utilise uniquement les valeurs explicitement fournies par l'utilisateur : "
        "n'invente, ne déduis, ne génère et ne reprends aucun exemple pour un champ requis. "
        "Si la réponse ne fournit pas clairement tous les champs demandés, pose à nouveau "
        "la question et n'appelle pas l'outil. Sinon, fusionne les valeurs aux options "
        "existantes, puis appelle l'outil."
    )


def _generic_tool_error_message() -> str:
    return "L’opération n’a pas abouti. Vérifiez les informations fournies et réessayez."


def _is_abandonment(message: str) -> bool:
    """Recognize a short, explicit request to stop the pending operation."""
    normalized = message.strip().casefold()
    return normalized in {"annule", "annuler", "abandonne", "abandonner", "cancel", "cancelled"}
