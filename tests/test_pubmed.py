from datetime import date
from pathlib import Path

from baiodigest.config import SearchQuery, Settings
from baiodigest.fetchers.pubmed import PubmedClient, parse_pubmed_xml


class _PagingPubmedClient(PubmedClient):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def _get_json(self, path: str, params: dict[str, str]) -> dict:  # type: ignore[override]
        assert path == "esearch.fcgi"
        retstart = int(params["retstart"])
        if retstart == 0:
            return {"esearchresult": {"count": "3", "idlist": ["1", "2"]}}
        if retstart == 2:
            return {"esearchresult": {"count": "3", "idlist": ["3"]}}
        return {"esearchresult": {"count": "3", "idlist": []}}


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


def test_search_ids_handles_pagination() -> None:
    settings = Settings()
    client = _PagingPubmedClient(settings)

    ids = client.search_ids(
        SearchQuery(name="test", terms="enzyme engineering"),
        start=date(2026, 3, 1),
        end=date(2026, 3, 1),
    )

    client.close()

    assert ids == ["1", "2", "3"]
