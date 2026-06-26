"""Centralized, typed application settings.

All configuration is read from environment variables (or a local `.env` file).
Import the ready-to-use singleton: `from config import settings`.
"""

from __future__ import annotations

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
