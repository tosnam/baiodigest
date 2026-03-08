from baiodigest.models import NewsletterIssue, NewsletterItem, NewsletterSection
from baiodigest.newsletters.summarize import build_newsletter_prompt, validate_summary_coverage


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


def test_validate_summary_coverage_flags_missing_story_titles() -> None:
    expected_titles = ["A", "B", "C"]
    covered_titles = ["A", "B"]

    result = validate_summary_coverage(expected_titles, covered_titles)

    assert result.missing_titles == ["C"]
    assert result.is_complete is False
