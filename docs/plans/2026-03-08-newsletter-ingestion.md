# Newsletter Ingestion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Gmail-based Nature and Science newsletter ingestion, summarize each issue without omitting main stories, and replace the homepage archive preview with newsletter sections while preserving the existing PubMed pipeline.

**Architecture:** Keep the PubMed paper pipeline unchanged and add a separate newsletter ingestion path with its own models, Gmail fetcher, source-specific parsers, summarization flow, and static pages. The site generator will read both data sets and render them side by side, with the homepage showing newsletter sections instead of the archive preview list.

**Tech Stack:** Python 3.12, Gmail API, `google-api-python-client`, `google-auth-oauthlib`, pytest, Jinja2, existing baioDigest models and static site generator

---

### Task 1: Add newsletter settings and serialization models

**Files:**
- Modify: `src/baiodigest/config.py`
- Modify: `src/baiodigest/models.py`
- Create: `tests/test_newsletter_models.py`

**Step 1: Write the failing test**

```python
from baiodigest.models import NewsletterIssue, NewsletterSection, NewsletterItem, NewsletterSummary


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
                items=[NewsletterItem(title="Story A", url="https://example.com/a", snippet="A", section_name="Top stories")]
            )
        ],
        summary=NewsletterSummary(
            overview="overview",
            highlights=["Story A summary"],
            significance="importance",
            covered_item_titles=["Story A"],
        ),
        raw_metadata={"from": "Nature Briefing <news@nature.com>"},
    )

    loaded = NewsletterIssue.from_json(issue.to_json())

    assert loaded.message_id == "gmail-123"
    assert loaded.sections[0].items[0].title == "Story A"
    assert loaded.summary.covered_item_titles == ["Story A"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_newsletter_models.py::test_newsletter_issue_round_trips_json -v`
Expected: FAIL with import or attribute errors for missing newsletter model types.

**Step 3: Write minimal implementation**

```python
Source = Literal["pubmed"]
NewsletterSource = Literal["nature", "science"]


@dataclass(slots=True)
class NewsletterItem:
    title: str
    url: str
    snippet: str
    section_name: str


@dataclass(slots=True)
class NewsletterSection:
    heading: str
    items: list[NewsletterItem]


@dataclass(slots=True)
class NewsletterSummary:
    overview: str
    highlights: list[str]
    significance: str
    covered_item_titles: list[str]


@dataclass(slots=True)
class NewsletterIssue:
    ...
```

Add newsletter-related settings to `Settings`, including:
- Gmail credentials/token paths
- Gmail label names for Nature and Science
- Newsletter data directory

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_newsletter_models.py::test_newsletter_issue_round_trips_json -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/config.py src/baiodigest/models.py tests/test_newsletter_models.py
git commit -m "feat: add newsletter models and settings"
```

### Task 2: Add Gmail message fetching and checkpoint persistence

**Files:**
- Create: `src/baiodigest/newsletters/gmail_client.py`
- Create: `src/baiodigest/newsletters/state.py`
- Create: `src/baiodigest/newsletters/__init__.py`
- Create: `tests/test_newsletter_gmail_client.py`

**Step 1: Write the failing test**

```python
from baiodigest.newsletters.gmail_client import extract_html_body, list_labeled_message_ids


def test_extract_html_body_prefers_html_part() -> None:
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/plain", "body": {"data": "cGxhaW4="}},
            {"mimeType": "text/html", "body": {"data": "PGgxPkhlbGxvPC9oMT4="}},
        ],
    }

    assert extract_html_body(payload) == "<h1>Hello</h1>"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_newsletter_gmail_client.py::test_extract_html_body_prefers_html_part -v`
Expected: FAIL because the Gmail client module does not exist.

**Step 3: Write minimal implementation**

```python
def extract_html_body(payload: dict) -> str | None:
    if payload.get("mimeType") == "text/html":
        return _decode_body(payload["body"]["data"])
    for part in payload.get("parts", []):
        html = extract_html_body(part)
        if html:
            return html
    return None
```

Implement:
- OAuth credential loading for Gmail API using readonly scope
- list messages by label
- get message by id
- persistent checkpoint helpers storing last processed internal date or history boundary

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_newsletter_gmail_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/newsletters/__init__.py src/baiodigest/newsletters/gmail_client.py src/baiodigest/newsletters/state.py tests/test_newsletter_gmail_client.py
git commit -m "feat: add gmail newsletter ingestion client"
```

### Task 3: Add Nature and Science newsletter parsers

**Files:**
- Create: `src/baiodigest/newsletters/parsers.py`
- Create: `tests/fixtures/nature_newsletter.html`
- Create: `tests/fixtures/science_newsletter.html`
- Create: `tests/test_newsletter_parsers.py`

**Step 1: Write the failing tests**

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_newsletter_parsers.py -v`
Expected: FAIL because parser functions do not exist.

**Step 3: Write minimal implementation**

```python
def parse_nature_issue(*, message_id: str, thread_id: str, subject: str, html: str) -> NewsletterIssue:
    soup = BeautifulSoup(html, "html.parser")
    sections = _extract_sections(soup, source="nature")
    return NewsletterIssue(...)
```

Implement:
- source-specific parser entry points
- shared helpers for heading/item extraction
- fallback handling when sections are shallow or malformed
- canonical title and source naming

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_newsletter_parsers.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/newsletters/parsers.py tests/fixtures/nature_newsletter.html tests/fixtures/science_newsletter.html tests/test_newsletter_parsers.py
git commit -m "feat: parse nature and science newsletters"
```

### Task 4: Add newsletter summarization with story-coverage validation

**Files:**
- Modify: `src/baiodigest/summarizer/prompts.py`
- Create: `src/baiodigest/newsletters/summarize.py`
- Create: `tests/test_newsletter_summarize.py`

**Step 1: Write the failing tests**

```python
from baiodigest.models import NewsletterIssue, NewsletterSection, NewsletterItem
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_newsletter_summarize.py -v`
Expected: FAIL because summarization helpers do not exist.

**Step 3: Write minimal implementation**

```python
def build_newsletter_prompt(issue: NewsletterIssue) -> str:
    return (
        "Summarize every main article in this newsletter. "
        "Do not omit any primary story. "
        f"Detected items: {', '.join(_main_item_titles(issue))}"
    )
```

Implement:
- prompt builder for newsletter issues
- response parser into `NewsletterSummary`
- coverage validation comparing parsed main item titles with covered titles in the summary
- retry or pending-status behavior when coverage is incomplete

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_newsletter_summarize.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/summarizer/prompts.py src/baiodigest/newsletters/summarize.py tests/test_newsletter_summarize.py
git commit -m "feat: add newsletter summarization coverage checks"
```

### Task 5: Add newsletter fetch CLI and JSON persistence

**Files:**
- Create: `src/baiodigest/newsletters/fetch.py`
- Modify: `src/baiodigest/newsletters/__init__.py`
- Create: `tests/test_newsletter_fetch.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from baiodigest.newsletters.fetch import save_issue
from baiodigest.models import NewsletterIssue


def test_save_issue_writes_source_scoped_json(tmp_path: Path, newsletter_issue: NewsletterIssue) -> None:
    path = save_issue(newsletter_issue, tmp_path)

    assert path == tmp_path / "nature" / "gmail-123.json"
    assert path.exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_newsletter_fetch.py::test_save_issue_writes_source_scoped_json -v`
Expected: FAIL because the fetch module does not exist.

**Step 3: Write minimal implementation**

```python
def save_issue(issue: NewsletterIssue, base_dir: Path) -> Path:
    path = base_dir / issue.source / f"{issue.message_id}.json"
    issue.to_file(path)
    return path
```

Implement:
- newsletter fetch CLI entry point
- source label iteration
- deduplication by existing JSON files
- parser dispatch
- summarization invocation
- partial-save behavior for pending summaries

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_newsletter_fetch.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/newsletters/__init__.py src/baiodigest/newsletters/fetch.py tests/test_newsletter_fetch.py
git commit -m "feat: add newsletter fetch pipeline"
```

### Task 6: Extend the site generator and templates for newsletters

**Files:**
- Modify: `src/baiodigest/generator/site.py`
- Modify: `templates/base.html`
- Modify: `templates/index.html`
- Create: `templates/newsletters.html`
- Create: `templates/newsletter_source.html`
- Create: `templates/newsletter_issue.html`
- Modify: `tests/test_site_generation.py`

**Step 1: Write the failing site test**

```python
def test_index_renders_newsletter_sections_instead_of_archive_preview(tmp_path: Path) -> None:
    generator = StaticSiteGenerator(...)
    generator.generate()

    index_html = (tmp_path / "docs" / "index.html").read_text(encoding="utf-8")

    assert "Newsletter Briefings" in index_html
    assert "Archive preview" not in index_html
    assert "Nature" in index_html
    assert "Science" in index_html
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_site_generation.py::test_index_renders_newsletter_sections_instead_of_archive_preview -v`
Expected: FAIL because newsletter rendering is not implemented.

**Step 3: Write minimal implementation**

```python
@dataclass(slots=True)
class SiteContext:
    digests: list[DailyDigest]
    queries: list[SearchQuery]
    newsletter_issues: list[NewsletterIssue]
```

Implement:
- newsletter loading helpers
- per-source grouping for latest issues
- home page newsletter blocks
- newsletter index and source pages
- issue detail pages
- base navigation link to newsletters

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_site_generation.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/generator/site.py templates/base.html templates/index.html templates/newsletters.html templates/newsletter_source.html templates/newsletter_issue.html tests/test_site_generation.py
git commit -m "feat: render newsletter pages in static site"
```

### Task 7: Wire docs, dependencies, and end-to-end command flow

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `scripts/run-daily.sh`
- Create: `tests/test_repo_metadata.py`

**Step 1: Write the failing metadata or docs-facing test**

```python
from pathlib import Path


def test_readme_mentions_newsletter_fetch_command() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "python -m baiodigest.newsletters.fetch" in readme
    assert "Gmail API" in readme
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_repo_metadata.py::test_readme_mentions_newsletter_fetch_command -v`
Expected: FAIL until docs and command references are updated.

**Step 3: Write minimal implementation**

```toml
[project]
dependencies = [
  "httpx>=0.27.0",
  "jinja2>=3.1.4",
  "tenacity>=9.0.0",
  "google-api-python-client>=2.0.0",
  "google-auth-oauthlib>=1.0.0",
]
```

Update:
- dependency list
- README setup steps for Gmail OAuth, labels, and fetch command
- daily script order so newsletter fetch runs before site generation or before notification, whichever is appropriate

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_repo_metadata.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml README.md scripts/run-daily.sh tests/test_repo_metadata.py
git commit -m "docs: document newsletter ingestion workflow"
```

### Task 8: Full verification before integration

**Files:**
- Verify only

**Step 1: Run targeted newsletter tests**

Run: `pytest tests/test_newsletter_models.py tests/test_newsletter_gmail_client.py tests/test_newsletter_parsers.py tests/test_newsletter_summarize.py tests/test_newsletter_fetch.py -v`
Expected: PASS

**Step 2: Run site generation coverage**

Run: `pytest tests/test_site_generation.py -v`
Expected: PASS

**Step 3: Run full suite**

Run: `pytest -v`
Expected: PASS with no regressions in existing PubMed digest behavior.

**Step 4: Build a local preview**

Run: `BAIODIGEST_DOCS_DIR=preview uv run python -m baiodigest.main --generate-only`
Expected: site rebuild succeeds and includes newsletter navigation and sections.

**Step 5: Commit final verification checkpoint**

```bash
git status --short
git add -A
git commit -m "feat: add newsletter ingestion and rendering"
```
