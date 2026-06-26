"""RAG retrieval tool — searches the Qdrant knowledge base built from the XML.

The returned string lists each retrieved chunk with its similarity score and
source metadata. Because this string is the tool's output, the Chainlit tool step
shows exactly which chunks were retrieved — no frontend coupling required.
"""

from __future__ import annotations

from langchain_core.tools import tool

from agent.tools.registry import register
from rag.embeddings import embed_query
from rag.store import QdrantStore

# Lazy connection; no network call happens until the tool is actually used.
_store = QdrantStore()


@register
@tool
def search_knowledge_base(query: str, k: int = 5) -> str:
    """Search the XML knowledge base for passages relevant to `query`.

    Returns up to `k` chunks, each with a similarity score and source metadata
    (file, record id). Use this whenever the user's question might be answered by
    the ingested data.
    """
    hits = _store.search(embed_query(query), k=k)
    if not hits:
        return "No matching passages found in the knowledge base."

    blocks = []
    for index, hit in enumerate(hits, start=1):
        blocks.append(
            f"[{index}] score={hit.score:.3f} "
            f"source={hit.source_file} record={hit.record_id} "
            f"tag={hit.tag} chunk={hit.chunk_index}\n"
            f"{hit.text}"
        )
    return "\n\n".join(blocks)
