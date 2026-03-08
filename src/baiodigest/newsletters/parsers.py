from __future__ import annotations

from html import unescape
import re

from baiodigest.models import NewsletterIssue, NewsletterItem, NewsletterSection


SECTION_RE = re.compile(
    r'<section[^>]*data-newsletter-section="(?P<heading>[^"]+)"[^>]*>(?P<body>.*?)</section>',
    re.DOTALL | re.IGNORECASE,
)
NATURE_BLOCK_RE = re.compile(
    r"<h2>\s*<a[^>]+href=\"(?P<url>[^\"]+)\"[^>]*>(?P<title>.*?)</a>\s*</h2>\s*<p[^>]*>(?P<snippet>.*?)</p>",
    re.DOTALL | re.IGNORECASE,
)
SCIENCE_TITLE_CARD_RE = re.compile(
    r"<td[^>]*(?:class=\"[^\"]*em_f24[^\"]*\"|style=\"[^\"]*font:\s*600\s*22px/28px[^\"]*\")[^>]*>\s*<a[^>]+href=\"(?P<url>[^\"]+)\"[^>]*>(?P<title>.*?)</a>\s*</td>",
    re.DOTALL | re.IGNORECASE,
)
SCIENCE_BODY_BLOCK_RE = re.compile(
    r"<td[^>]*style=\"[^\"]*font:\s*(?:400\s+)?(?:16px/24px|18px/27px)\s*'PT Serif'[^\"]*\"[^>]*>(?P<body>.*?)</td>",
    re.DOTALL | re.IGNORECASE,
)
ARTICLE_RE = re.compile(
    r"<article[^>]*>.*?<a[^>]*href=\"(?P<url>[^\"]+)\"[^>]*>(?P<title>.*?)</a>.*?(?:<p[^>]*>(?P<snippet>.*?)</p>)?.*?</article>",
    re.DOTALL | re.IGNORECASE,
)
ANCHOR_RE = re.compile(r"<a[^>]+href=\"(?P<url>[^\"]+)\"[^>]*>(?P<title>.*?)</a>", re.DOTALL | re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
H1_RE = re.compile(r"<h1[^>]*>(?P<title>.*?)</h1>", re.DOTALL | re.IGNORECASE)
STYLE_SCRIPT_RE = re.compile(r"<(?:style|script)\b[^>]*>.*?</(?:style|script)>", re.DOTALL | re.IGNORECASE)
SKIP_TITLE_PATTERNS = (
    "view this email in your browser",
    "unsubscribe",
    "manage your preferences",
    "privacy policy",
    "advertisement",
    "click here to forward it by e-mail",
    "nature | ",
    "science translational medicine",
    "submit it to ask science",
)


def _clean_html_text(value: str) -> str:
    without_style = STYLE_SCRIPT_RE.sub(" ", value)
    collapsed = TAG_RE.sub(" ", without_style)
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


def _extract_nature_blocks(html: str, section_name: str) -> list[NewsletterItem]:
    items: list[NewsletterItem] = []
    for match in NATURE_BLOCK_RE.finditer(html):
        title = _clean_html_text(match.group("title"))
        url = match.group("url").strip()
        snippet = _clean_html_text(match.group("snippet"))
        normalized_title = title.lower()
        if not title or not url:
            continue
        if any(pattern in normalized_title for pattern in SKIP_TITLE_PATTERNS):
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


def _extract_science_cards(html: str, section_name: str) -> list[NewsletterItem]:
    items: list[NewsletterItem] = []
    seen_titles: set[str] = set()
    for match in SCIENCE_TITLE_CARD_RE.finditer(html):
        title = _clean_html_text(match.group("title"))
        url = match.group("url").strip()
        normalized_title = title.lower()
        if not title or not url:
            continue
        if any(pattern in normalized_title for pattern in SKIP_TITLE_PATTERNS):
            continue
        if title in seen_titles:
            continue
        seen_titles.add(title)
        items.append(
            NewsletterItem(
                title=title,
                url=url,
                snippet="",
                section_name=section_name,
            )
        )
    return items


def _extract_science_body_links(html: str, section_name: str) -> list[NewsletterItem]:
    items: list[NewsletterItem] = []
    seen_titles: set[str] = set()
    for block in SCIENCE_BODY_BLOCK_RE.finditer(html):
        for match in ANCHOR_RE.finditer(block.group("body")):
            title = _clean_html_text(match.group("title"))
            url = match.group("url").strip()
            normalized_title = title.lower()
            if not title or not url:
                continue
            if len(title) < 20:
                continue
            if any(pattern in normalized_title for pattern in SKIP_TITLE_PATTERNS):
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)
            items.append(
                NewsletterItem(
                    title=title,
                    url=url,
                    snippet="",
                    section_name=section_name,
                )
            )
            break
    return items


def _extract_anchor_items(html: str, section_name: str) -> list[NewsletterItem]:
    items: list[NewsletterItem] = []
    seen_titles: set[str] = set()
    for match in ANCHOR_RE.finditer(html):
        title = _clean_html_text(match.group("title"))
        url = match.group("url").strip()
        normalized_title = title.lower()
        if not title or not url:
            continue
        if len(title) < 20:
            continue
        if any(pattern in normalized_title for pattern in SKIP_TITLE_PATTERNS):
            continue
        if title in seen_titles:
            continue
        seen_titles.add(title)
        items.append(
            NewsletterItem(
                title=title,
                url=url,
                snippet="",
                section_name=section_name,
            )
        )
    return items


def _extract_sections(html: str, source: str) -> list[NewsletterSection]:
    sections: list[NewsletterSection] = []
    source_items: list[NewsletterItem] = []
    if source == "nature":
        source_items = _extract_nature_blocks(html, "Top stories")
    elif source == "science":
        source_items = _extract_science_cards(html, "Top stories")
        body_items = _extract_science_body_links(html, "Top stories")
        seen_titles = {item.title for item in source_items}
        for item in body_items:
            if item.title not in seen_titles:
                source_items.append(item)
                seen_titles.add(item.title)

    if source_items:
        return [NewsletterSection(heading="Top stories", items=source_items)]

    for match in SECTION_RE.finditer(html):
        heading = _clean_html_text(match.group("heading"))
        items = _extract_items(match.group("body"), heading)
        if items:
            sections.append(NewsletterSection(heading=heading, items=items))

    if sections:
        return sections

    fallback_items = _extract_items(html, "Top stories")
    if not fallback_items:
        fallback_items = _extract_anchor_items(html, "Top stories")
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
    sections = _extract_sections(html, source)
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
