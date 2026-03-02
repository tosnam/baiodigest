from baiodigest.fetchers import merge_papers
from baiodigest.models import Paper


def _paper(title: str, doi: str | None, source_id: str | None = None) -> Paper:
    return Paper(
        title=title,
        abstract="abstract",
        authors=["A"],
        affiliations=["Aff"],
        doi=doi,
        source="pubmed",
        source_type="published",
        journal="J",
        url="https://example.org",
        category="bioengineering",
        date="2026-03-01",
        mesh_terms=[],
        source_id=source_id,
    )


def test_merge_papers_dedup_by_pubmed_source_id() -> None:
    first = _paper("Title one", "10.1/first", source_id="12345")
    second = _paper("Different title", None, source_id="12345")

    merged = merge_papers([[first], [second]])

    assert len(merged) == 1
    assert merged[0].source_id == "12345"


def test_merge_papers_dedup_by_doi() -> None:
    first = _paper("Title one", "10.1/example", source_id=None)
    second = _paper("Title one updated", "10.1/example", source_id=None)

    merged = merge_papers([[first], [second]])

    assert len(merged) == 1


def test_merge_papers_dedup_by_title_hash() -> None:
    one = _paper("AI-guided Enzyme Engineering", None)
    two = _paper("AI guided enzyme engineering!!", None)

    merged = merge_papers([[one], [two]])

    assert len(merged) == 1
