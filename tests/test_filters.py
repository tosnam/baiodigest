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


def _paper(title: str, abstract: str) -> Paper:
    return Paper(
        title=title,
        abstract=abstract,
        authors=["A"],
        affiliations=[],
        doi=None,
        source="biorxiv",
        source_type="preprint",
        journal="bioRxiv",
        url="https://example.org",
        category="bioengineering",
        date="2026-03-01",
        mesh_terms=[],
    )


def test_keyword_filter_requires_two_matches() -> None:
    settings = Settings()
    paper = _paper("Protein engineering study", "this work improves enzyme activity")

    result = keyword_filter(paper, settings)

    assert result.relevant
    assert len(result.matched_keywords) >= 2


def test_llm_filter_fail_open_after_parse_errors() -> None:
    settings = Settings()
    paper = _paper(
        "Protein engineering with AI",
        "This enzyme project applies machine learning and directed evolution to improve activity.",
    )

    passed, keyword_count = filter_papers([paper], settings, _BrokenThenValidOllama())

    assert keyword_count == 1
    assert len(passed) == 1
    assert passed[0][1].category == "fallback"


def test_llm_filter_accepts_high_confidence() -> None:
    settings = Settings()
    paper = _paper(
        "Protein engineering with AI",
        "This enzyme project applies machine learning and directed evolution to improve activity.",
    )

    passed, keyword_count = filter_papers([paper], settings, _ValidOllama())

    assert keyword_count == 1
    assert len(passed) == 1
    assert passed[0][1].category == "ai_enzyme"
