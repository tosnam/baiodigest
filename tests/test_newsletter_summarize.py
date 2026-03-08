from baiodigest.models import NewsletterIssue, NewsletterItem, NewsletterSection
from baiodigest.newsletters.summarize import (
    build_newsletter_prompt,
    parse_newsletter_summary,
    summarize_issue_payload,
    validate_summary_coverage,
)


def test_prompt_explicitly_requires_covering_all_main_items() -> None:
    issue = NewsletterIssue(
        source="nature",
        newsletter_name="Nature Briefing",
        message_id="m1",
        thread_id="t1",
        received_at="2026-03-08T00:00:00+00:00",
        published_at="2026-03-08",
        title="Issue",
        canonical_url="",
        html_body="",
        text_body="",
        sections=[
            NewsletterSection(
                heading="Top stories",
                items=[
                    NewsletterItem(title="A", url="https://a", snippet="a", section_name="Top stories"),
                    NewsletterItem(title="B", url="https://b", snippet="b", section_name="Top stories"),
                ],
            )
        ],
        summary=None,
        raw_metadata={},
    )

    prompt = build_newsletter_prompt(issue)

    assert "every main article" in prompt.lower()
    assert "do not omit" in prompt.lower()
    assert "article_briefings" in prompt
    assert "1-2 sentences" in prompt


def test_prompt_uses_structured_section_content_instead_of_raw_body_dump() -> None:
    issue = NewsletterIssue(
        source="nature",
        newsletter_name="Nature Briefing",
        message_id="m9",
        thread_id="t9",
        received_at="2026-03-08T00:00:00+00:00",
        published_at="2026-03-08",
        title="Issue",
        canonical_url="",
        html_body="",
        text_body="RAW BODY NOISE SHOULD NOT DOMINATE",
        sections=[
            NewsletterSection(
                heading="Top stories",
                items=[
                    NewsletterItem(title="A", url="https://a", snippet="Snippet A", section_name="Top stories"),
                ],
            )
        ],
        summary=None,
        raw_metadata={},
    )

    prompt = build_newsletter_prompt(issue)

    assert "Snippet A" in prompt
    assert "RAW BODY NOISE SHOULD NOT DOMINATE" not in prompt
    assert "https://a" in prompt


def test_prompt_truncates_overlong_snippets() -> None:
    issue = NewsletterIssue(
        source="nature",
        newsletter_name="Nature Briefing",
        message_id="m11",
        thread_id="t11",
        received_at="2026-03-08T00:00:00+00:00",
        published_at="2026-03-08",
        title="Issue",
        canonical_url="",
        html_body="",
        text_body="",
        sections=[
            NewsletterSection(
                heading="Top stories",
                items=[
                    NewsletterItem(
                        title="A",
                        url="https://a",
                        snippet=("long snippet " * 80).strip(),
                        section_name="Top stories",
                    ),
                ],
            )
        ],
        summary=None,
        raw_metadata={},
    )

    prompt = build_newsletter_prompt(issue)

    assert "long snippet long snippet long snippet" in prompt
    assert ("long snippet " * 30).strip() not in prompt


def test_validate_summary_coverage_flags_missing_story_titles() -> None:
    expected_titles = ["A", "B", "C"]
    covered_titles = ["A", "B"]

    result = validate_summary_coverage(expected_titles, covered_titles)

    assert result.missing_titles == ["C"]
    assert result.is_complete is False


def test_validate_summary_coverage_tolerates_minor_title_drift() -> None:
    expected_titles = ["An alleged nuclear blast may reignite weapons testing, and who owns the Moon"]
    covered_titles = ["알leged nuclear blast may reignite weapons testing, and who owns the Moon"]

    result = validate_summary_coverage(expected_titles, covered_titles)

    assert result.missing_titles == []
    assert result.is_complete is True


def test_parse_newsletter_summary_reads_article_briefings() -> None:
    summary = parse_newsletter_summary(
        {
            "overview": "전체 요약",
            "covered_item_titles": ["A"],
            "article_briefings": [
                {
                    "title": "A",
                    "url": "https://a",
                    "briefing_ko": "한글 브리핑",
                }
            ],
        }
    )

    assert summary.article_briefings[0].title == "A"
    assert summary.article_briefings[0].url == "https://a"
    assert summary.article_briefings[0].briefing_ko == "한글 브리핑"


def test_summarize_issue_payload_fills_missing_article_briefing_urls() -> None:
    issue = NewsletterIssue(
        source="nature",
        newsletter_name="Nature Briefing",
        message_id="m10",
        thread_id="t10",
        received_at="2026-03-08T00:00:00+00:00",
        published_at="2026-03-08",
        title="Issue",
        canonical_url="",
        html_body="",
        text_body="",
        sections=[
            NewsletterSection(
                heading="Top stories",
                items=[
                    NewsletterItem(title="A", url="https://a", snippet="Snippet A", section_name="Top stories"),
                ],
            )
        ],
        summary=None,
        raw_metadata={},
    )

    summary, coverage = summarize_issue_payload(
        issue,
        {
            "overview": "전체 요약",
            "article_briefings": [{"title": "A", "url": "", "briefing_ko": "한글 브리핑"}],
        },
    )

    assert summary.article_briefings[0].url == "https://a"
    assert coverage.is_complete is True
