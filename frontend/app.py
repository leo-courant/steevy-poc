"""Chainlit frontend.

Runs the backend deep agent in-process and bridges its LangGraph event stream
into the Chainlit UI:

  * every tool call becomes an expandable `cl.Step` showing its input and output
    (for `search_knowledge_base`, the output lists the retrieved chunks with their
    source metadata and similarity score);
  * the assistant's answer streams token-by-token into the chat message.
"""

from __future__ import annotations

import chainlit as cl

from agent.agent import build_agent


@cl.on_chat_start
async def on_chat_start() -> None:
    # Build the agent once per chat session.
    cl.user_session.set("agent", build_agent())
    await cl.Message(
        content=(
            "### 👋 Hi! Welcome to **Steevie's POC**\n\n"
            "Ask a question about the documents in the knowledge base — I'll "
            "search them and answer with sources.\n\n"
            "_Tip: expand the **tool step** above any answer to see the exact "
            "chunks I retrieved (with their source and similarity score)._"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    agent = cl.user_session.get("agent")
    # The agent may stream some assistant text *before* it decides to call a tool.
    # We only want the FINAL answer (streamed after the last tool call) to remain,
    # so it renders below the tool steps. Any text streamed before a tool starts is
    # discarded when that tool begins.
    answer: cl.Message | None = None
    open_steps: dict[str, cl.Step] = {}

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": message.content}]},
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

        elif kind == "on_chat_model_stream":
            token = _as_text(event["data"].get("chunk"))
            if token:
                if answer is None:
                    answer = cl.Message(content="")
                await answer.stream_token(token)

    if answer is not None:
        await answer.send()


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
