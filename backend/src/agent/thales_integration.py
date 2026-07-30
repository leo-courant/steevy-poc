"""Build the Thales-hosted chat model (OpenAI-compatible gateway).

Mirrors the working setup in `rag_mvp`: an explicit `ChatOpenAI` instance with
the gateway base URL, API key, CA bundle, and optional corporate proxy.

Passing an instance (rather than an `openai:...` string) to
`deepagents.create_deep_agent` matters: for string models deepagents forces
`use_responses_api=True`, which routes calls to the `/responses` endpoint the
Thales gateway does not implement. The instance below pins the classic
`/chat/completions` endpoint.

Secrets (API key, certificate contents) are never stored in the repository —
the user provides them via `.env` and `data/static/`.
"""
from __future__ import annotations

import os
import ssl
from pathlib import Path
from typing import Any

import httpx
from langchain_openai import ChatOpenAI


def configure_thales_environment(settings: Any) -> None:
    """Prepare non-secret local state: the tiktoken cache directory."""
    cache_dir = Path(settings.tiktoken_cache_dir)
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Best-effort: libraries fall back to their default cache location.
        pass
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(cache_dir))


def _http_client_kwargs(settings: Any) -> dict[str, Any]:
    """TLS/proxy options shared by the sync and async HTTP clients."""
    kwargs: dict[str, Any] = {}
    ca_path = Path(getattr(settings, "thales_ca_bundle", "") or "")
    if ca_path.name and ca_path.exists():
        # The Thales .crt holds only the server's leaf certificate, not a
        # full chain up to a self-signed root. curl accepts that (partial
        # chain); Python needs VERIFY_X509_PARTIAL_CHAIN to do the same.
        ctx = ssl.create_default_context(cafile=str(ca_path))
        ctx.verify_flags |= ssl.VERIFY_X509_PARTIAL_CHAIN
        kwargs["verify"] = ctx
    if getattr(settings, "thales_proxy", ""):
        kwargs["proxy"] = settings.thales_proxy
    return kwargs


def build_thales_chat_model(
    settings: Any, http_client: httpx.Client | None = None
) -> ChatOpenAI:
    """Return a `ChatOpenAI` bound to the Thales gateway (chat completions)."""
    kwargs = _http_client_kwargs(settings)
    return ChatOpenAI(
        model=settings.thales_chat_model,
        temperature=0.0,
        api_key=settings.thales_api_key,
        base_url=settings.thales_base_url,
        # Chainlit drives the agent through async streaming, so both clients
        # must trust the Thales CA bundle (and use the proxy when set).
        http_client=http_client or (httpx.Client(**kwargs) if kwargs else None),
        http_async_client=httpx.AsyncClient(**kwargs) if kwargs else None,
        # Skip langchain-openai's TCP-keepalive transport injection: it is
        # unused with custom clients and only triggers a spurious
        # "proxy auto-detection disabled" warning when a system proxy exists.
        http_socket_options=(),
        use_responses_api=False,
    )


__all__ = ["build_thales_chat_model", "configure_thales_environment"]
