from pathlib import Path

from baiodigest.models import NewsletterIssue
from baiodigest.newsletters.fetch import save_issue


def test_save_issue_writes_source_scoped_json(tmp_path: Path) -> None:
    issue = NewsletterIssue(
        source="nature",
        newsletter_name="Nature Briefing",
        message_id="gmail-123",
        thread_id="thread-123",
        received_at="2026-03-08T06:30:00+00:00",
        published_at="2026-03-08",
        title="Issue",
        canonical_url="https://example.com/issue",
        html_body="<html></html>",
        text_body="plain text",
        sections=[],
        summary=None,
        raw_metadata={},
    )

    path = save_issue(issue, tmp_path)

    assert path == tmp_path / "nature" / "gmail-123.json"
    assert path.exists()
