from __future__ import annotations

from dataclasses import dataclass
import difflib
import json
import re
import unicodedata

from baiodigest.models import NewsletterArticleBriefing, NewsletterIssue, NewsletterSummary
from baiodigest.summarizer.prompts import build_newsletter_summary_prompt


@dataclass(slots=True, frozen=True)
class CoverageValidation:
    is_complete: bool
    missing_titles: list[str]


def _main_item_titles(issue: NewsletterIssue) -> list[str]:
    titles: list[str] = []
    for section in issue.sections:
        for item in section.items:
            normalized = item.title.strip()
            if normalized and normalized not in titles:
                titles.append(normalized)
    return titles


def _main_item_urls(issue: NewsletterIssue) -> dict[str, str]:
    urls: dict[str, str] = {}
    for section in issue.sections:
        for item in section.items:
            title = item.title.strip()
            if title and item.url.strip() and title not in urls:
                urls[title] = item.url.strip()
    return urls


def _compact_snippet(snippet: str, limit: int = 260) -> str:
    cleaned = re.sub(r"\s+", " ", snippet).strip()
    if len(cleaned) <= limit:
        return cleaned
    truncated = cleaned[: limit - 1].rsplit(" ", 1)[0].strip()
    return f"{truncated}…"


def build_newsletter_prompt(issue: NewsletterIssue) -> str:
    lines = []
    body_lines = []
    for section in issue.sections:
        for item in section.items:
            lines.append(f"- [{section.heading}] {item.title} ({item.url})")
            snippet = _compact_snippet(item.snippet)
            if snippet:
                body_lines.append(f"[{section.heading}] {item.title} ({item.url}): {snippet}")
            else:
                body_lines.append(f"[{section.heading}] {item.title} ({item.url})")
    item_lines = "\n".join(lines) if lines else "- No parsed items"
    body = "\n".join(body_lines) if body_lines else issue.text_body
    return build_newsletter_summary_prompt(
        newsletter_name=issue.newsletter_name,
        title=issue.title,
        item_lines=item_lines,
        body=body,
    )


def parse_newsletter_summary(payload: dict) -> NewsletterSummary:
    article_briefings = [
        NewsletterArticleBriefing(
            title=str(item.get("title", "")).strip(),
            url=str(item.get("url", "")).strip(),
            briefing_ko=str(item.get("briefing_ko", "")).strip(),
        )
        for item in payload.get("article_briefings", [])
        if isinstance(item, dict) and str(item.get("title", "")).strip()
    ]
    covered_titles = [str(item).strip() for item in payload.get("covered_item_titles", []) if str(item).strip()]
    if not covered_titles:
        covered_titles = [item.title for item in article_briefings if item.title]
    return NewsletterSummary(
        overview=str(payload.get("overview", "")).strip(),
        highlights=[str(item).strip() for item in payload.get("highlights", []) if str(item).strip()],
        significance=str(payload.get("significance", "")).strip(),
        covered_item_titles=covered_titles,
        article_briefings=article_briefings,
    )


def parse_newsletter_summary_json(raw: str) -> NewsletterSummary:
    return parse_newsletter_summary(json.loads(raw))


def _normalize_title(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title).casefold()
    ascii_text = "".join(
        char if char.isascii() and (char.isalnum() or char.isspace()) else " " for char in normalized
    )
    return re.sub(r"\s+", " ", ascii_text).strip()


def _title_overlap_ratio(left: str, right: str) -> float:
    left_tokens = {token for token in _normalize_title(left).split() if len(token) > 1}
    right_tokens = {token for token in _normalize_title(right).split() if len(token) > 1}
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens)


def _title_match_score(expected_title: str, covered_title: str) -> float:
    normalized_expected = _normalize_title(expected_title)
    normalized_covered = _normalize_title(covered_title)
    if not normalized_expected or not normalized_covered:
        return 0.0
    if normalized_expected == normalized_covered:
        return 1.0
    sequence_ratio = difflib.SequenceMatcher(None, normalized_expected, normalized_covered).ratio()
    overlap_ratio = _title_overlap_ratio(expected_title, covered_title)
    if overlap_ratio < 0.75:
        return 0.0
    return sequence_ratio


def validate_summary_coverage(expected_titles: list[str], covered_titles: list[str]) -> CoverageValidation:
    normalized_covered = [title.strip() for title in covered_titles if title.strip()]
    used_indexes: set[int] = set()
    missing: list[str] = []
    for expected_title in expected_titles:
        normalized_expected = expected_title.strip()
        if not normalized_expected:
            continue
        best_index = None
        best_score = 0.0
        for index, covered_title in enumerate(normalized_covered):
            if index in used_indexes:
                continue
            score = _title_match_score(normalized_expected, covered_title)
            if score > best_score:
                best_score = score
                best_index = index
        if best_index is None or best_score < 0.9:
            missing.append(normalized_expected)
            continue
        used_indexes.add(best_index)
    return CoverageValidation(is_complete=not missing, missing_titles=missing)


def summarize_issue_payload(issue: NewsletterIssue, payload: dict) -> tuple[NewsletterSummary, CoverageValidation]:
    summary = parse_newsletter_summary(payload)
    item_urls = _main_item_urls(issue)
    normalized_briefings: list[NewsletterArticleBriefing] = []
    for briefing in summary.article_briefings:
        url = briefing.url.strip()
        if not url:
            for item_title, item_url in item_urls.items():
                if _title_match_score(briefing.title, item_title) >= 0.9:
                    url = item_url
                    break
        normalized_briefings.append(
            NewsletterArticleBriefing(
                title=briefing.title,
                url=url,
                briefing_ko=briefing.briefing_ko,
            )
        )
    summary.article_briefings = normalized_briefings
    coverage = validate_summary_coverage(_main_item_titles(issue), summary.covered_item_titles)
    return summary, coverage
