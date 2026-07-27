from pathlib import Path

from rag.parsing import parse_file


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_XML = REPOSITORY_ROOT / "data/rag/sample.xml"


def test_boats_are_indexed_as_individual_records_with_labelled_fields() -> None:
    records = parse_file(SAMPLE_XML)
    records_by_id = {record.record_id: record for record in records}

    assert "boats-0" not in records_by_id
    boat = records_by_id["AF787"]
    assert boat.tag == "boat"
    assert "record_type: boat" in boat.text
    assert "record_id: AF787" in boat.text
    assert "attributes: id: AF787" in boat.text
    assert "owner.firstName: Kylian" in boat.text
    assert "owner.lastName: Mbappé" in boat.text


def test_incident_text_includes_its_identifier_and_field_names() -> None:
    records_by_id = {record.record_id: record for record in parse_file(SAMPLE_XML)}
    incident = records_by_id["I207"]

    assert incident.tag == "incidentLog"
    assert "record_type: incidentLog" in incident.text
    assert "record_id: I207" in incident.text
    assert "boatRef: B207" in incident.text
    assert "actionsTaken.towed: To medical berth" in incident.text
    assert incident.metadata["boatRef"] == "B207"
    assert incident.metadata["actionsTaken.towed"] == "To medical berth"