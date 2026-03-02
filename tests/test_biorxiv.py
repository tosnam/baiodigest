import json
from pathlib import Path

from baiodigest.fetchers.biorxiv import parse_biorxiv_collection


def test_parse_biorxiv_collection_fixture() -> None:
    fixture = Path("tests/fixtures/biorxiv_sample.json")
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    papers = parse_biorxiv_collection(payload["collection"], {"bioengineering"})

    assert len(papers) == 1
    paper = papers[0]
    assert paper.source == "biorxiv"
    assert paper.source_type == "preprint"
    assert paper.doi == "10.1101/2026.03.01.123456"
    assert "AI-guided" in paper.title
