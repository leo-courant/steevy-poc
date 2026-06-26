"""Split records into overlapping chunks.

The chunking strategy lives entirely in `chunk_text`. To change how the corpus
is chunked (e.g. token-based, or one-chunk-per-record), edit that one function.
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.parsing import Record


@dataclass
class Chunk:
    """A single embeddable passage plus the metadata needed to cite it."""

    text: str
    source_file: str
    record_id: str
    tag: str
    chunk_index: int


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Greedy character window over whitespace, with character overlap.

    Words are never split. Each chunk grows until adding the next word would
    exceed `chunk_size` characters; the following chunk is seeded with the
    trailing `overlap` characters of the previous one for context continuity.
    """
    if chunk_size <= 0:
        return [text]

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    current: list[str] = []
    length = 0

    for word in words:
        addition = len(word) + (1 if current else 0)
        if current and length + addition > chunk_size:
            chunks.append(" ".join(current))
            current, length = _overlap_tail(current, overlap)
            addition = len(word) + (1 if current else 0)
        current.append(word)
        length += addition

    if current:
        chunks.append(" ".join(current))
    return chunks


def _overlap_tail(words: list[str], overlap: int) -> tuple[list[str], int]:
    """Return the trailing words that fit within `overlap` characters."""
    tail: list[str] = []
    length = 0
    for word in reversed(words):
        addition = len(word) + (1 if tail else 0)
        if length + addition > overlap:
            break
        tail.insert(0, word)
        length += addition
    return tail, length


def chunk_records(records: list[Record], chunk_size: int, overlap: int) -> list[Chunk]:
    """Flatten records into chunks, preserving each record's source metadata."""
    chunks: list[Chunk] = []
    for record in records:
        for index, piece in enumerate(chunk_text(record.text, chunk_size, overlap)):
            chunks.append(
                Chunk(
                    text=piece,
                    source_file=record.source_file,
                    record_id=record.record_id,
                    tag=record.tag,
                    chunk_index=index,
                )
            )
    return chunks
