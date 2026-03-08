from baiodigest.models import (
    NewsletterArticleBriefing,
    NewsletterIssue,
    NewsletterItem,
    NewsletterSection,
    NewsletterSummary,
)


def test_newsletter_issue_round_trips_json() -> None:
    issue = NewsletterIssue(
        source="nature",
        newsletter_name="Nature Briefing",
        message_id="gmail-123",
        thread_id="thread-123",
        received_at="2026-03-08T06:30:00+00:00",
        published_at="2026-03-08",
        title="Nature Briefing: Cancer and AI",
        canonical_url="https://example.com/issue",
        html_body="<html></html>",
        text_body="plain text",
        sections=[
            NewsletterSection(
                heading="Top stories",
                items=[
                    NewsletterItem(
                        title="Story A",
                        url="https://example.com/a",
                        snippet="A",
                        section_name="Top stories",
                    )
                ],
            )
        ],
        summary=NewsletterSummary(
            overview="overview",
            highlights=["Story A summary"],
            significance="importance",
            covered_item_titles=["Story A"],
            article_briefings=[
                NewsletterArticleBriefing(
                    title="Story A",
                    url="https://example.com/a",
                    briefing_ko="스토리 A 한글 브리핑",
                )
            ],
        ),
        raw_metadata={"from": "Nature Briefing <news@nature.com>"},
    )

    loaded = NewsletterIssue.from_json(issue.to_json())

    assert loaded.message_id == "gmail-123"
    assert loaded.sections[0].items[0].title == "Story A"
    assert loaded.summary is not None
    assert loaded.summary.covered_item_titles == ["Story A"]
    assert loaded.summary.article_briefings[0].briefing_ko == "스토리 A 한글 브리핑"
