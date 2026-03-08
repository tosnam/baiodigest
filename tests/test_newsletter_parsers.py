from pathlib import Path

from baiodigest.newsletters.parsers import parse_nature_issue, parse_science_issue


def test_parse_nature_issue_extracts_multiple_main_items() -> None:
    html = Path("tests/fixtures/nature_newsletter.html").read_text(encoding="utf-8")

    issue = parse_nature_issue(message_id="m1", thread_id="t1", subject="Nature Briefing", html=html)

    assert issue.source == "nature"
    assert len(issue.sections) >= 1
    assert sum(len(section.items) for section in issue.sections) >= 3


def test_parse_science_issue_extracts_multiple_main_items() -> None:
    html = Path("tests/fixtures/science_newsletter.html").read_text(encoding="utf-8")

    issue = parse_science_issue(message_id="m2", thread_id="t2", subject="Science", html=html)

    assert issue.source == "science"
    assert sum(len(section.items) for section in issue.sections) >= 3
