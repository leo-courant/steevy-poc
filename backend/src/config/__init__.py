"""Centralized, typed application settings.

All configuration is read from environment variables (or a local `.env` file).
Import the ready-to-use singleton: `from config import settings`.
"""

from __future__ import annotations

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for every tunable in the project."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- App (Chainlit) ---
    app_port: int = 8000

    # --- Agent LLM ---
    # `provider:model` string consumed by deepagents / LangChain init_chat_model.
    agent_model: str = "openai:gpt-4o"
    openai_api_key: str = ""

    # --- Thales LLM (optional) ---
    # Provide the Thales-compatible base URL (OpenAI-compatible endpoint).
    # When set, the agent uses the Thales gateway instead of `agent_model`.
    thales_base_url: str = ""
    # Thales API key (kept empty by default; user will populate locally).
    thales_api_key: str = ""
    # Model name exposed by the Thales gateway (see also apim/mistral-small).
    thales_chat_model: str = "apim/mistral-large"
    # Corporate proxy to reach the gateway, if required on your network
    # (e.g. http://timtam.au.thalesgroup.local:8080). Leave blank for none.
    thales_proxy: str = ""
    # Path to the Thales CA bundle (do NOT commit certificate contents).
    thales_ca_bundle: str = os.path.join("data", "static", "genai.tatm.thales.crt")
    # Local cache directory for tiktoken (non-secret asset)
    tiktoken_cache_dir: str = os.path.join("data", "static", "tiktoken_cache")

    # --- Embeddings (local FastEmbed, no API key) ---
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # --- Qdrant ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = "local-dev-key"
    qdrant_collection: str = "xml_knowledge_base"

    # --- RAG / ingestion ---
    rag_data_dir: str = "data/rag"
    rag_record_tag: str = ""  # blank => use the root's direct children as records
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 100


settings = Settings()

# Ensure a place for tiktoken cache is available to libraries that consult
# `TIKTOKEN_CACHE_DIR`. We do not validate presence of any certificate or API
# key here — the user will provide those privately later.
os.environ.setdefault("TIKTOKEN_CACHE_DIR", settings.tiktoken_cache_dir)
