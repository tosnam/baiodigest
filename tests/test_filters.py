from baiodigest.config import Settings
from baiodigest.filters.relevance import filter_papers, keyword_filter
from baiodigest.models import Paper


class _BrokenThenValidOllama:
    def __init__(self) -> None:
        self.calls = 0

    def classify_relevance(self, title: str, abstract: str):
        self.calls += 1
        raise ValueError("invalid json")


class _ValidOllama:
    class Decision:
        relevant = True
        confidence = 0.9
        category = "ai_enzyme"
        reason = "useful"

    def classify_relevance(self, title: str, abstract: str):
        return self.Decision()


def _paper(title: str, abstract: str, matched_query_names: list[str] | None = None) -> Paper:
    return Paper(
        title=title,
        abstract=abstract,
        authors=["A"],
        affiliations=[],
        doi=None,
        source="pubmed",
        source_type="published",
        journal="Journal",
        url="https://example.org",
        category="bioengineering",
        date="2026-03-01",
        mesh_terms=[],
        matched_query_names=matched_query_names or [],
    )


def test_prefilter_passes_when_no_excluded_keyword() -> None:
    settings = Settings()
    paper = _paper(
        "Interesting study",
        "This study improves enzyme production in yeast",
        matched_query_names=["enzyme/protein engineering + AI"],
    )

    result = keyword_filter(paper, settings)

    assert result.relevant
    assert result.category == "prefilter"
    assert result.matched_keywords == ["enzyme/protein engineering + AI"]


def test_prefilter_blocks_excluded_keyword() -> None:
    settings = Settings()
    paper = _paper("Clinical trial report", "A randomized clinical trial with epidemiology data")

    result = keyword_filter(paper, settings)

    assert not result.relevant
    assert result.category == "excluded"


def test_llm_filter_fail_open_after_parse_errors() -> None:
    settings = Settings()
    paper = _paper(
        "Protein engineering with AI",
        "This enzyme project applies machine learning and directed evolution to improve activity.",
    )

    passed, prefilter_count = filter_papers([paper], settings, _BrokenThenValidOllama())

    assert prefilter_count == 1
    assert len(passed) == 1
    assert passed[0][1].category == "fallback"


def test_llm_filter_accepts_high_confidence() -> None:
    settings = Settings()
    paper = _paper(
        "Protein engineering with AI",
        "This enzyme project applies machine learning and directed evolution to improve activity.",
    )

    passed, prefilter_count = filter_papers([paper], settings, _ValidOllama())

    assert prefilter_count == 1
    assert len(passed) == 1
    assert passed[0][1].category == "ai_enzyme"
