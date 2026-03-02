from __future__ import annotations

from collections.abc import Iterable
import logging

from baiodigest.config import Settings
from baiodigest.models import FilterResult, Paper
from baiodigest.summarizer.ollama import OllamaClient

logger = logging.getLogger(__name__)


def _contains(text: str, keyword: str) -> bool:
    return keyword.lower() in text


def keyword_filter(paper: Paper, settings: Settings) -> FilterResult:
    haystack = f"{paper.title} {paper.abstract}".lower()
    excluded = [kw for kw in settings.exclude_keywords if _contains(haystack, kw)]
    matched_queries = sorted(set(paper.matched_query_names))

    if excluded:
        return FilterResult(
            relevant=False,
            confidence=1.0,
            category="excluded",
            reason=f"Excluded keyword matched: {', '.join(excluded)}",
            matched_keywords=matched_queries,
        )

    return FilterResult(
        relevant=True,
        confidence=1.0,
        category="prefilter",
        reason="Exclude prefilter passed",
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
            return FilterResult(
                relevant=is_relevant,
                confidence=decision.confidence,
                category=decision.category,
                reason=decision.reason,
                matched_keywords=keyword_result.matched_keywords,
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
    reason = "LLM JSON parsing failed twice; fail-open applied"
    if last_error:
        reason = f"{reason}: {last_error}"

    return FilterResult(
        relevant=True,
        confidence=1.0,
        category="fallback",
        reason=reason,
        matched_keywords=keyword_result.matched_keywords,
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
