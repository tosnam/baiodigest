from baiodigest.fetchers import merge_papers
from baiodigest.models import Paper


def _paper(title: str, doi: str | None, source: str, source_type: str) -> Paper:
    return Paper(
        title=title,
        abstract="abstract",
        authors=["A"],
        affiliations=["Aff"],
        doi=doi,
        source=source,
        source_type=source_type,
        journal="J",
        url="https://example.org",
        category="bioengineering",
        date="2026-03-01",
        mesh_terms=[],
    )


def test_merge_papers_dedup_by_doi_prefers_published() -> None:
    preprint = _paper("Title one", "10.1/example", "biorxiv", "preprint")
    published = _paper("Title one", "10.1/example", "pubmed", "published")

    merged = merge_papers([[preprint], [published]])

    assert len(merged) == 1
    assert merged[0].source == "pubmed"


def test_merge_papers_dedup_by_title_hash() -> None:
    one = _paper("AI-guided Enzyme Engineering", None, "biorxiv", "preprint")
    two = _paper("AI guided enzyme engineering!!", None, "pubmed", "published")

    merged = merge_papers([[one], [two]])

    assert len(merged) == 1
