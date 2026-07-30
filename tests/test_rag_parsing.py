from pathlib import Path

from rag.parsing import parse_file


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_XML = REPOSITORY_ROOT / "data/rag/sample.xml"


def _record_with_id(records, element_id: str):
    return next(r for r in records if f"attributes: id: {element_id}" in r.text)


def test_boats_are_indexed_as_individual_records_with_labelled_fields() -> None:
    records = parse_file(SAMPLE_XML)

    # The <boats> container is unwrapped: no record is the container itself.
    assert all("record_type: boats" not in record.text for record in records)

    boat = _record_with_id(records, "AF787")
    assert boat.tag == "boat"
    assert boat.source_file == "sample.xml"
    assert "record_type: boat" in boat.text
    assert "owner.firstName: Kylian" in boat.text
    assert "owner.lastName: Mbappé" in boat.text


def test_incident_text_includes_its_identifier_and_field_names() -> None:
    records = parse_file(SAMPLE_XML)
    incident = _record_with_id(records, "I207")

    assert incident.tag == "incidentLog"
    assert "record_type: incidentLog" in incident.text
    assert "boatRef: B207" in incident.text
    assert "actionsTaken.towed: To medical berth" in incident.text


def test_records_expose_only_semantic_search_fields() -> None:
    record = parse_file(SAMPLE_XML)[0]

    # Exact-search remnants are gone: everything searchable lives in `text`.
    assert not hasattr(record, "metadata")
    assert not hasattr(record, "record_id")
