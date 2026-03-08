from __future__ import annotations

from dataclasses import dataclass
import json

from baiodigest.models import NewsletterIssue, NewsletterSummary
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


def build_newsletter_prompt(issue: NewsletterIssue) -> str:
    lines = []
    for section in issue.sections:
        for item in section.items:
            lines.append(f"- [{section.heading}] {item.title}")
    item_lines = "\n".join(lines) if lines else "- No parsed items"
    return build_newsletter_summary_prompt(
        newsletter_name=issue.newsletter_name,
        title=issue.title,
        item_lines=item_lines,
        body=issue.text_body,
    )


def parse_newsletter_summary(payload: dict) -> NewsletterSummary:
    return NewsletterSummary(
        overview=str(payload.get("overview", "")).strip(),
        highlights=[str(item).strip() for item in payload.get("highlights", []) if str(item).strip()],
        significance=str(payload.get("significance", "")).strip(),
        covered_item_titles=[
            str(item).strip() for item in payload.get("covered_item_titles", []) if str(item).strip()
        ],
    )


def parse_newsletter_summary_json(raw: str) -> NewsletterSummary:
    return parse_newsletter_summary(json.loads(raw))


def validate_summary_coverage(expected_titles: list[str], covered_titles: list[str]) -> CoverageValidation:
    normalized_covered = {title.strip() for title in covered_titles if title.strip()}
    missing = [title for title in expected_titles if title.strip() and title.strip() not in normalized_covered]
    return CoverageValidation(is_complete=not missing, missing_titles=missing)


def summarize_issue_payload(issue: NewsletterIssue, payload: dict) -> tuple[NewsletterSummary, CoverageValidation]:
    summary = parse_newsletter_summary(payload)
    coverage = validate_summary_coverage(_main_item_titles(issue), summary.covered_item_titles)
    return summary, coverage
