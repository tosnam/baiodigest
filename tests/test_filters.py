from baiodigest.config import Settings
from baiodigest.filters.relevance import filter_papers, keyword_filter, llm_relevance_filter
from baiodigest.models import FilterResult, Paper
from baiodigest.summarizer.ollama import OllamaClient, RelevanceDecision


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
        topic_tags = ["other"]
        problem_tags = ["general_insight"]
        research_type = "basic"
        practical_distance = "foundational"

    def classify_relevance(self, title: str, abstract: str):
        return self.Decision()


class _EnglishReasonOllama:
    class Decision:
        relevant = True
        confidence = 0.82
        category = "protein_engineering"
        reason = "This paper has industrial relevance"
        topic_tags = ["other"]
        problem_tags = ["general_insight"]
        research_type = "basic"
        practical_distance = "foundational"

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
    assert "다음 단계" in result.reason


def test_prefilter_blocks_excluded_keyword() -> None:
    settings = Settings()
    paper = _paper("Clinical trial report", "A randomized clinical trial with epidemiology data")

    result = keyword_filter(paper, settings)

    assert not result.relevant
    assert result.category == "excluded"
    assert "제외" in result.reason


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
    assert "누락 방지" in passed[0][1].reason


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
    assert "관련 논문" in passed[0][1].reason


def test_llm_reason_is_forced_to_korean() -> None:
    settings = Settings()
    paper = _paper(
        "Enzyme optimization",
        "Machine learning is used to optimize enzyme yield.",
    )

    passed, _ = filter_papers([paper], settings, _EnglishReasonOllama())

    assert len(passed) == 1
    assert "관련 논문" in passed[0][1].reason


def test_llm_relevance_filter_preserves_research_radar_fields() -> None:
    settings = Settings()
    paper = _paper(
        "Protein engineering with AI",
        "This enzyme project applies machine learning and directed evolution to improve activity.",
    )
    keyword_result = FilterResult(
        relevant=True,
        confidence=1.0,
        category="prefilter",
        reason="prefilter pass",
        matched_keywords=["enzyme"],
    )

    class _RadarOllama:
        def classify_relevance(self, title: str, abstract: str) -> RelevanceDecision:
            return RelevanceDecision(
                relevant=True,
                confidence=0.82,
                category="ai_enzyme",
                reason="산업적 활용 가능성이 있다.",
                topic_tags=["ai_protein_design"],
                problem_tags=["stability"],
                research_type="method",
                practical_distance="mid_term",
            )

    result = llm_relevance_filter(paper, keyword_result, _RadarOllama(), settings)

    assert result.topic_tags == ["ai_protein_design"]
    assert result.problem_tags == ["stability"]
    assert result.research_type == "method"
    assert result.practical_distance == "mid_term"


def test_summarize_reads_research_radar_notes() -> None:
    settings = Settings()
    client = OllamaClient(settings)
    client._generate = lambda prompt: (
        '{"background":"배경","method":"방법","result":"결과","significance":"의미",'
        '"why_it_matters":"읽을 가치가 있다.","novelty_note":"새 방법이다.",'
        '"application_note":"공정에 참고 가능하다.","caution_note":"스케일업 검증 필요"}'
    )

    summary = client.summarize("title", "abstract")

    assert summary.why_it_matters == "읽을 가치가 있다."
    assert summary.application_note == "공정에 참고 가능하다."
    assert summary.caution_note == "스케일업 검증 필요"
