"""Parse XML file(s) into flat records (text + source metadata).

A *record* is one logical unit of the knowledge base. By default each direct
child of the XML root becomes a record; set `record_tag` to instead treat every
element with that tag (anywhere in the tree) as a record.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Record:
    """One logical unit extracted from an XML file."""
    tag: str
    text: str
    source_file: str


def _element_text(element: ET.Element) -> str:
    """Render an XML record as labelled text suitable for embedding.

    XML tag names and attributes convey important meaning.  Keeping them in the
    text lets a semantic search distinguish values while preserving the complete leaf content.
    """
    lines = [f"record_type: {element.tag}"]
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


def parse_file(path: Path, record_tag: str | None = None) -> list[Record]:
    """Parse a single XML file into records."""
    root = ET.parse(path).getroot()
    elements = _record_elements(root, record_tag)

    records: list[Record] = []
    for element in elements:
        text = _element_text(element)
        if not text:
            continue
        records.append(
            Record(
                tag=element.tag,
                text=text,
                source_file=path.name,
            )
        )
    return records


def parse_dir(data_dir: Path, record_tag: str | None = None) -> list[Record]:
    """Parse every `*.xml` file in a directory into a flat list of records."""
    records: list[Record] = []
    for xml_path in sorted(data_dir.glob("*.xml")):
        records.extend(parse_file(xml_path, record_tag))
    return records


if __name__ == "__main__":
    xml_path = Path("data/rag/sample.xml")

    print("=" * 80)
    print("1. Chargement du XML")
    print("=" * 80)

    root = ET.parse(xml_path).getroot()
    print(f"Root tag : {root.tag}")

    print("\n")

    print("=" * 80)
    print("2. Test _record_elements()")
    print("=" * 80)

    elements = _record_elements(root, None)

    print(f"Nombre d'éléments trouvés : {len(elements)}")

    for i, element in enumerate(elements, start=1):
        print(f"[{i}] tag={element.tag}")

    print("\n")

    if elements:
        first_element = elements[0]

        print("=" * 80)
        print("3. Test _element_text() sur le premier élément")
        print("=" * 80)

        text = _element_text(first_element)
        print(text)

        print("\n")

    print("=" * 80)
    print("4. Test parse_file()")
    print("=" * 80)

    records = parse_file(xml_path)

    print(f"Nombre de records : {len(records)}")

    for i, record in enumerate(records, start=1):
        print("\n" + "-" * 80)
        print(f"RECORD #{i}")
        print("-" * 80)

        print(f"tag         : {record.tag}")
        print(f"source_file : {record.source_file}")

        print("\nTEXT")
        print(record.text)

        break

    print("\n")
    print("=" * 80)
    print("FIN DES TESTS")
    print("=" * 80)
