from __future__ import annotations

from html import unescape
import re

from baiodigest.models import NewsletterIssue, NewsletterItem, NewsletterSection


SECTION_RE = re.compile(
    r'<section[^>]*data-newsletter-section="(?P<heading>[^"]+)"[^>]*>(?P<body>.*?)</section>',
    re.DOTALL | re.IGNORECASE,
)
ARTICLE_RE = re.compile(
    r"<article[^>]*>.*?<a[^>]*href=\"(?P<url>[^\"]+)\"[^>]*>(?P<title>.*?)</a>.*?(?:<p[^>]*>(?P<snippet>.*?)</p>)?.*?</article>",
    re.DOTALL | re.IGNORECASE,
)
TAG_RE = re.compile(r"<[^>]+>")
H1_RE = re.compile(r"<h1[^>]*>(?P<title>.*?)</h1>", re.DOTALL | re.IGNORECASE)


def _clean_html_text(value: str) -> str:
    collapsed = TAG_RE.sub(" ", value)
    return " ".join(unescape(collapsed).split())


def _extract_items(html: str, section_name: str) -> list[NewsletterItem]:
    items: list[NewsletterItem] = []
    for match in ARTICLE_RE.finditer(html):
        title = _clean_html_text(match.group("title"))
        url = match.group("url").strip()
        snippet = _clean_html_text(match.group("snippet") or "")
        if not title or not url:
            continue
        items.append(
            NewsletterItem(
                title=title,
                url=url,
                snippet=snippet,
                section_name=section_name,
            )
        )
    return items


def _extract_sections(html: str) -> list[NewsletterSection]:
    sections: list[NewsletterSection] = []
    for match in SECTION_RE.finditer(html):
        heading = _clean_html_text(match.group("heading"))
        items = _extract_items(match.group("body"), heading)
        if items:
            sections.append(NewsletterSection(heading=heading, items=items))

    if sections:
        return sections

    fallback_items = _extract_items(html, "Top stories")
    if fallback_items:
        return [NewsletterSection(heading="Top stories", items=fallback_items)]

    return []


def _extract_title(html: str, fallback: str) -> str:
    match = H1_RE.search(html)
    if match:
        title = _clean_html_text(match.group("title"))
        if title:
            return title
    return fallback


def _build_issue(source: str, newsletter_name: str, message_id: str, thread_id: str, subject: str, html: str) -> NewsletterIssue:
    sections = _extract_sections(html)
    first_url = ""
    for section in sections:
        if section.items:
            first_url = section.items[0].url
            break

    return NewsletterIssue(
        source=source,
        newsletter_name=newsletter_name,
        message_id=message_id,
        thread_id=thread_id,
        received_at="",
        published_at="",
        title=_extract_title(html, subject),
        canonical_url=first_url,
        html_body=html,
        text_body=_clean_html_text(html),
        sections=sections,
        raw_metadata={"subject": subject},
    )


def parse_nature_issue(*, message_id: str, thread_id: str, subject: str, html: str) -> NewsletterIssue:
    return _build_issue(
        source="nature",
        newsletter_name="Nature Briefing",
        message_id=message_id,
        thread_id=thread_id,
        subject=subject,
        html=html,
    )


def parse_science_issue(*, message_id: str, thread_id: str, subject: str, html: str) -> NewsletterIssue:
    return _build_issue(
        source="science",
        newsletter_name="Science Newsletter",
        message_id=message_id,
        thread_id=thread_id,
        subject=subject,
        html=html,
    )
