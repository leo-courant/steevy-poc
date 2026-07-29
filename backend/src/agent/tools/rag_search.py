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

# import re
# _LOOKUP_VALUE_PATTERN = re.compile(r"[\w.+@-]{2,}")

def _format_hits(hits: list, retrieval: str) -> str:
    """Format retrieved chunks for the agent and the Chainlit tool step."""
    blocks = []
    for index, hit in enumerate(hits, start=1):
        blocks.append(
            f"[{index}] score={hit.score:.3f} retrieval={retrieval} "
            f"source={hit.source_file} record={hit.record_id} "
            f"tag={hit.tag} chunk={hit.chunk_index}\n"
            f"{hit.text}"
        )
    return "\n\n".join(blocks)


# def _unique_hits(hits: list) -> list:
#     """Remove chunks returned by multiple exact or semantic retrieval paths."""
#     unique = []
#     seen = set()
#     for hit in hits:
#         key = (hit.source_file, hit.record_id, hit.chunk_index)
#         if key not in seen:
#             unique.append(hit)
#             seen.add(key)
#     return unique


@register
@tool
def search_knowledge_base(query: str, k: int = 10) -> str:
    """Search the XML knowledge base for passages relevant to `query`.

    Returns up to `k` chunks, each with a similarity score and source metadata
    (file, record id). Use this whenever the user's question might be answered by
    the ingested data.
    """
    # Recherche exacte desactivee
    # lookup_values = list(dict.fromkeys(_LOOKUP_VALUE_PATTERN.findall(query)))
    # exact_hits = []
    # for value in lookup_values:
    #     exact_hits.extend(_store.find_by_record_id(value))
    #     exact_hits.extend(_store.find_by_lookup_value(value))
    # exact_hits = _unique_hits(exact_hits)
    # if exact_hits:
    #     return _format_hits(exact_hits, "exact_value")

    semantic_hits = _store.search(embed_query(query), k=k)
    if not semantic_hits:
        return "No matching passages found in the knowledge base."
    return _format_hits(semantic_hits, "semantic")
