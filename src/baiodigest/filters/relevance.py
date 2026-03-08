from __future__ import annotations

from collections.abc import Iterable
import logging
import re

from baiodigest.config import Settings
from baiodigest.models import FilterResult, Paper
from baiodigest.summarizer.ollama import OllamaClient

logger = logging.getLogger(__name__)


def _contains(text: str, keyword: str) -> bool:
    return keyword.lower() in text


def _contains_hangul(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text))


def _ensure_korean_reason(reason: str, *, relevant: bool) -> str:
    cleaned = " ".join(reason.split()).strip()
    if cleaned and _contains_hangul(cleaned):
        return cleaned
    if relevant:
        return "산업적 활용 가능성이 있어 관련 논문으로 판단했습니다."
    return "산업적 활용 가능성이 낮아 제외했습니다."


def keyword_filter(paper: Paper, settings: Settings) -> FilterResult:
    haystack = f"{paper.title} {paper.abstract}".lower()
    excluded = [kw for kw in settings.exclude_keywords if _contains(haystack, kw)]
    matched_queries = sorted(set(paper.matched_query_names))

    if excluded:
        return FilterResult(
            relevant=False,
            confidence=1.0,
            category="excluded",
            reason=f"제외 키워드가 감지되어 제외했습니다: {', '.join(excluded)}",
            matched_keywords=matched_queries,
        )

    return FilterResult(
        relevant=True,
        confidence=1.0,
        category="prefilter",
        reason="제외 키워드가 없어 다음 단계로 진행했습니다.",
        matched_keywords=matched_queries,
    )


def llm_relevance_filter(
    paper: Paper,
    keyword_result: FilterResult,
    ollama: OllamaClient,
    settings: Settings,
) -> FilterResult:
    if not keyword_result.relevant:
        return keyword_result

    last_error: Exception | None = None
    for attempt in (1, 2):
        try:
            decision = ollama.classify_relevance(paper.title, paper.abstract)
            is_relevant = bool(decision.relevant and decision.confidence >= settings.relevance_threshold)
            korean_reason = _ensure_korean_reason(decision.reason, relevant=is_relevant)
            return FilterResult(
                relevant=is_relevant,
                confidence=decision.confidence,
                category=decision.category,
                reason=korean_reason,
                matched_keywords=keyword_result.matched_keywords,
                topic_tags=decision.topic_tags or ["other"],
                problem_tags=decision.problem_tags or ["general_insight"],
                research_type=decision.research_type or "basic",
                practical_distance=decision.practical_distance or "foundational",
            )
        except Exception as exc:
            last_error = exc
            logger.warning(
                "LLM relevance parsing failed for '%s' (attempt %d/2): %s",
                paper.title,
                attempt,
                exc,
            )

    # Fail-open to avoid dropping potentially relevant papers.
    reason = "LLM 판정 응답을 해석하지 못해 누락 방지를 위해 포함했습니다."

    return FilterResult(
        relevant=True,
        confidence=1.0,
        category="fallback",
        reason=reason,
        matched_keywords=keyword_result.matched_keywords,
        topic_tags=["other"],
        problem_tags=["general_insight"],
        research_type="basic",
        practical_distance="foundational",
    )


def filter_papers(
    papers: Iterable[Paper],
    settings: Settings,
    ollama: OllamaClient,
) -> tuple[list[tuple[Paper, FilterResult]], int]:
    passed: list[tuple[Paper, FilterResult]] = []
    prefilter_pass_count = 0

    for paper in papers:
        keyword_result = keyword_filter(paper, settings)
        if not keyword_result.relevant:
            continue

        prefilter_pass_count += 1
        llm_result = llm_relevance_filter(paper, keyword_result, ollama, settings)
        if llm_result.relevant:
            passed.append((paper, llm_result))

    return passed, prefilter_pass_count
