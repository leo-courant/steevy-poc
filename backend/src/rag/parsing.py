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


def _element_text(element: ET.Element, record_id: str) -> str:
    """Render an XML record as labelled text suitable for embedding.

    XML tag names and attributes convey important meaning.  Keeping them in the
    text lets a semantic search distinguish values such as a boat reference
    from an incident identifier, while preserving the complete leaf content.
    """
    lines = [f"record_type: {element.tag}", f"record_id: {record_id}"]
    if element.attrib:
        attributes = ", ".join(
            f"{name}: {value}" for name, value in element.attrib.items()
        )
        lines.append(f"attributes: {attributes}")

    def visit(node: ET.Element, path: str) -> None:
        children = list(node)
        if not children:
            value = (node.text or "").strip()
            lines.append(f"{path}: {value or '(empty)'}")
            return

        for child in children:
            visit(child, f"{path}.{child.tag}" if path else child.tag)

    for child in element:
        visit(child, child.tag)
    return "\n".join(lines)


def _record_elements(root: ET.Element, record_tag: str | None) -> list[ET.Element]:
    """Return logical records, unwrapping a repeated-record container once."""
    if record_tag:
        return list(root.iter(record_tag))

    elements: list[ET.Element] = []
    for child in root:
        grandchildren = list(child)
        is_repeated_container = (
            len(grandchildren) > 0
            and len({grandchild.tag for grandchild in grandchildren}) == 1
            and any(list(grandchild) for grandchild in grandchildren)
        )
        elements.extend(grandchildren if is_repeated_container else [child])
    return elements


def _element_fields(element: ET.Element) -> dict[str, str]:
    """Extract leaf XML values by their relative field path for exact filters."""
    fields: dict[str, str] = {}

    def visit(node: ET.Element, path: str) -> None:
        children = list(node)
        if not children:
            value = (node.text or "").strip()
            if value:
                fields[path] = value
            return
        for child in children:
            visit(child, f"{path}.{child.tag}" if path else child.tag)

    for child in element:
        visit(child, child.tag)
    return fields


def parse_file(path: Path, record_tag: str | None = None) -> list[Record]:
    """Parse a single XML file into records."""
    root = ET.parse(path).getroot()
    elements = _record_elements(root, record_tag)

    records: list[Record] = []
    for index, element in enumerate(elements):
        record_id = (
            element.get("id")
            or element.get("code")
            or element.get("name")
            or f"{element.tag}-{index}"
        )
        text = _element_text(element, record_id)
        if not text:
            continue
        records.append(
            Record(
                record_id=record_id,
                tag=element.tag,
                text=text,
                source_file=path.name,
                metadata={**dict(element.attrib), **_element_fields(element)},
            )
        )
    return records


def parse_dir(data_dir: Path, record_tag: str | None = None) -> list[Record]:
    """Parse every `*.xml` file in a directory into a flat list of records."""
    records: list[Record] = []
    for xml_path in sorted(data_dir.glob("*.xml")):
        records.extend(parse_file(xml_path, record_tag))
    return records
