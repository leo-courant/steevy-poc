"""The Thales gateway only implements the OpenAI chat-completions endpoint.

deepagents' provider profile forces `use_responses_api=True` when the model is
given as an `openai:...` string, which routes every call to `/responses` and
fails against the gateway. These tests pin the fix: an explicit `ChatOpenAI`
instance that always talks to `/chat/completions`.
"""

from types import SimpleNamespace

import httpx

from agent.thales_integration import build_thales_chat_model

FAKE_SETTINGS = SimpleNamespace(
    thales_base_url="https://llm.genai.tatm.thales",
    thales_api_key="sk-test",
    thales_chat_model="apim/mistral-large",
    thales_ca_bundle="",
    thales_proxy="",
)

CHAT_COMPLETION_STUB = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "created": 0,
    "model": "apim/mistral-large",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "pong"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}


def test_thales_model_calls_chat_completions_not_responses() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return httpx.Response(200, json=CHAT_COMPLETION_STUB)

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    llm = build_thales_chat_model(FAKE_SETTINGS, http_client=http_client)

    reply = llm.invoke("ping")

    assert captured["path"].endswith("/chat/completions")
    assert reply.content == "pong"


def test_thales_model_uses_configured_key_and_model() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization", "")
        return httpx.Response(200, json=CHAT_COMPLETION_STUB)

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    llm = build_thales_chat_model(FAKE_SETTINGS, http_client=http_client)
    llm.invoke("ping")

    assert captured["auth"] == "Bearer sk-test"
    assert llm.model_name == "apim/mistral-large"
