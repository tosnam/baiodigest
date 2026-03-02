from pathlib import Path

from baiodigest.fetchers.pubmed import parse_pubmed_xml


def test_parse_pubmed_xml_fixture() -> None:
    fixture = Path("tests/fixtures/pubmed_sample.xml")
    xml_text = fixture.read_text(encoding="utf-8")

    papers = parse_pubmed_xml(xml_text)

    assert len(papers) == 1
    paper = papers[0]
    assert paper.source == "pubmed"
    assert paper.source_type == "published"
    assert paper.doi == "10.1000/example-doi"
    assert paper.date == "2026-03-01"
    assert paper.mesh_terms == ["Metabolic Engineering"]
