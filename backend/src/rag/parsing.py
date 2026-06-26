"""Parse XML file(s) into flat records (text + source metadata).

A *record* is one logical unit of the knowledge base. By default each direct
child of the XML root becomes a record; set `record_tag` to instead treat every
element with that tag (anywhere in the tree) as a record.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Record:
    """One logical unit extracted from an XML file."""

    record_id: str
    tag: str
    text: str
    source_file: str
    metadata: dict[str, str] = field(default_factory=dict)


def _element_text(element: ET.Element) -> str:
    """Concatenate all human-readable text inside an element (and descendants)."""
    parts = [t.strip() for t in element.itertext() if t and t.strip()]
    return "\n".join(parts)


def parse_file(path: Path, record_tag: str | None = None) -> list[Record]:
    """Parse a single XML file into records."""
    root = ET.parse(path).getroot()
    elements = list(root.iter(record_tag)) if record_tag else list(root)

    records: list[Record] = []
    for index, element in enumerate(elements):
        text = _element_text(element)
        if not text:
            continue
        record_id = element.get("id") or element.get("name") or f"{element.tag}-{index}"
        records.append(
            Record(
                record_id=record_id,
                tag=element.tag,
                text=text,
                source_file=path.name,
                metadata=dict(element.attrib),
            )
        )
    return records


def parse_dir(data_dir: Path, record_tag: str | None = None) -> list[Record]:
    """Parse every `*.xml` file in a directory into a flat list of records."""
    records: list[Record] = []
    for xml_path in sorted(data_dir.glob("*.xml")):
        records.extend(parse_file(xml_path, record_tag))
    return records
