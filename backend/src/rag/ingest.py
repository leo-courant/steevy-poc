"""Ingestion pipeline: data/rag/*.xml -> parse -> chunk -> embed -> Qdrant.

Run via `make index` (or `uv run python -m rag.ingest`). Re-running rebuilds the
collection from scratch with whatever XML is currently in the drop-zone.
"""

from __future__ import annotations

from pathlib import Path

from config import settings
from rag.chunking import chunk_records
from rag.embeddings import embed_texts
from rag.parsing import parse_dir
from rag.store import QdrantStore


def _lookup_values(record_id: str, fields: dict[str, str]) -> list[str]:
    """Build case-insensitive exact-match values from a record payload."""
    values = [record_id, *fields.values()]
    return list(
        dict.fromkeys(
            lookup_value
            for value in values
            for lookup_value in (value, value.casefold())
        )
    )


def run_ingestion() -> int:
    """Parse, chunk, embed, and upsert all XML in the data dir. Returns count."""
    data_dir = Path(settings.rag_data_dir)
    record_tag = settings.rag_record_tag or None

    records = parse_dir(data_dir, record_tag)
    print(f"Parsed {len(records)} records from {data_dir}/*.xml")

    chunks = chunk_records(records, settings.rag_chunk_size, settings.rag_chunk_overlap)
    print(f"Created {len(chunks)} chunks")
    if not chunks:
        print(f"Nothing to index. Add .xml files to '{data_dir}/' and re-run.")
        return 0

    vectors = embed_texts([chunk.text for chunk in chunks])
    payloads = [
        {
            "text": chunk.text,
            "source_file": chunk.source_file,
            "record_id": chunk.record_id,
            "tag": chunk.tag,
            "chunk_index": chunk.chunk_index,
            "fields": chunk.metadata,
            "lookup_values": _lookup_values(chunk.record_id, chunk.metadata),
        }
        for chunk in chunks
    ]

    store = QdrantStore()
    store.ensure_collection(vector_size=len(vectors[0]))
    count = store.upsert(vectors, payloads)
    print(f"Upserted {count} chunks into Qdrant collection '{store.collection}'")
    return count


if __name__ == "__main__":
    run_ingestion()
