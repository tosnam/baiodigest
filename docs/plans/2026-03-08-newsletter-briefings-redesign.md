# Newsletter Briefings Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Render newsletter issues as day-based briefing cards on the home page and convert newsletter issue pages to per-article Korean briefings.

**Architecture:** Keep Gmail ingestion and parser boundaries intact, but extend the newsletter summary model with article-level briefings and shift the site generator from source-grouped home rendering to issue-based rendering. The public issue template stops depending on whole-issue summary text and instead renders one Korean briefing per parsed main article.

**Tech Stack:** Python, dataclasses, Jinja2 templates, pytest, existing Ollama summary pipeline

---

### Task 1: Add failing tests for issue-centric home rendering

**Files:**
- Modify: `tests/test_site_generation.py`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

```python
def test_index_renders_one_newsletter_card_per_issue(tmp_path: Path) -> None:
    _write_sample_newsletter_issue(..., "nature", "nature-1", "Lead story")
    _write_sample_newsletter_issue(..., "nature", "nature-2", "Other story")
    generator.generate()
    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")
    assert index_html.count('class="digest-row"') == 3
    assert ">View<" in index_html
    assert "View all" not in index_html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_index_renders_one_newsletter_card_per_issue -v`
Expected: FAIL because the current index groups by source and still renders `View all`.

**Step 3: Write minimal implementation**

No production code in this task.

**Step 4: Run test to verify it still fails for the right reason**

Run: `uv run pytest tests/test_site_generation.py::test_index_renders_one_newsletter_card_per_issue -v`
Expected: FAIL with incorrect card count or missing `View`.

**Step 5: Commit**

```bash
git add tests/test_site_generation.py
git commit -m "test: cover issue-based newsletter cards"
```

### Task 2: Add failing tests for article-centric issue pages

**Files:**
- Modify: `tests/test_site_generation.py`
- Modify: `tests/test_newsletter_summarize.py`
- Test: `tests/test_site_generation.py`
- Test: `tests/test_newsletter_summarize.py`

**Step 1: Write the failing tests**

```python
def test_newsletter_issue_page_renders_article_briefings(tmp_path: Path) -> None:
    issue.summary = NewsletterSummary(
        overview="...",
        covered_item_titles=["Story A"],
        article_briefings=[
            {"title": "Story A", "url": "https://example.com/a", "briefing_ko": "한글 브리핑"}
        ],
    )
    generator.generate()
    html = (docs_dir / "newsletters" / "nature" / "nature-1.html").read_text(encoding="utf-8")
    assert "요약" not in html
    assert "Top stories" in html
    assert "Story A" in html
    assert "한글 브리핑" in html
```

```python
def test_validate_summary_coverage_uses_article_briefing_titles() -> None:
    ...
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_site_generation.py::test_newsletter_issue_page_renders_article_briefings tests/test_newsletter_summarize.py::test_validate_summary_coverage_uses_article_briefing_titles -v`
Expected: FAIL because `NewsletterSummary` does not yet support article briefing structures in rendering and validation.

**Step 3: Write minimal implementation**

No production code in this task.

**Step 4: Run tests to verify failure remains targeted**

Run the same command.
Expected: FAIL with missing field or old template output.

**Step 5: Commit**

```bash
git add tests/test_site_generation.py tests/test_newsletter_summarize.py
git commit -m "test: cover newsletter article briefing pages"
```

### Task 3: Extend newsletter summary models for article briefings

**Files:**
- Modify: `src/baiodigest/models.py`
- Modify: `tests/test_newsletter_models.py`
- Test: `tests/test_newsletter_models.py`

**Step 1: Write the failing test**

```python
def test_newsletter_summary_serializes_article_briefings() -> None:
    summary = NewsletterSummary(
        overview="overview",
        covered_item_titles=["Story A"],
        article_briefings=[
            NewsletterArticleBriefing(title="Story A", url="https://a", briefing_ko="요약")
        ],
    )
    ...
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_newsletter_models.py::test_newsletter_summary_serializes_article_briefings -v`
Expected: FAIL because the model lacks `article_briefings`.

**Step 3: Write minimal implementation**

```python
@dataclass(slots=True)
class NewsletterArticleBriefing:
    title: str
    url: str
    briefing_ko: str
```

Add list serialization/deserialization support inside `NewsletterSummary`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_newsletter_models.py::test_newsletter_summary_serializes_article_briefings -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/models.py tests/test_newsletter_models.py
git commit -m "feat: add newsletter article briefing model"
```

### Task 4: Change summary parsing and coverage validation to article-centric output

**Files:**
- Modify: `src/baiodigest/newsletters/summarize.py`
- Modify: `src/baiodigest/summarizer/prompts.py`
- Modify: `tests/test_newsletter_summarize.py`
- Test: `tests/test_newsletter_summarize.py`

**Step 1: Write the failing test**

```python
def test_parse_newsletter_summary_reads_article_briefings() -> None:
    payload = {
        "overview": "요약",
        "covered_item_titles": ["A"],
        "article_briefings": [
            {"title": "A", "url": "https://a", "briefing_ko": "한글 요약"}
        ],
    }
    summary = parse_newsletter_summary(payload)
    assert summary.article_briefings[0].briefing_ko == "한글 요약"
```

Add a second test asserting the prompt explicitly asks for one Korean briefing per main article.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_newsletter_summarize.py -v`
Expected: FAIL because the parser and prompt do not yet expose article briefing requirements.

**Step 3: Write minimal implementation**

Update the prompt contract and parse `article_briefings` into model objects while keeping `covered_item_titles` validation intact.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_newsletter_summarize.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/newsletters/summarize.py src/baiodigest/summarizer/prompts.py tests/test_newsletter_summarize.py
git commit -m "feat: summarize newsletters as article briefings"
```

### Task 5: Add display-name handling for newsletter issues

**Files:**
- Modify: `src/baiodigest/generator/site.py`
- Modify: `tests/test_site_generation.py`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

```python
def test_index_prefers_newsletter_name_for_display_title(tmp_path: Path) -> None:
    issue = _write_sample_newsletter_issue(...)
    issue.newsletter_name = "Nature Briefing: Microbiology"
    issue.title = "Lead story title"
    ...
    assert "Nature Briefing: Microbiology" in index_html
    assert "Lead story title" not in index_html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_index_prefers_newsletter_name_for_display_title -v`
Expected: FAIL because templates still use `issue.title`.

**Step 3: Write minimal implementation**

Add a display-title helper or property in site context/rendering that prefers branding metadata over subject-style issue titles.

**Step 4: Run test to verify it passes**

Run the same command.
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/generator/site.py tests/test_site_generation.py
git commit -m "feat: use newsletter branding for display titles"
```

### Task 6: Update home-page templates for issue-per-card rendering

**Files:**
- Modify: `templates/index.html`
- Modify: `static/style.css`
- Modify: `tests/test_site_generation.py`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

```python
def test_newsletter_briefings_heading_matches_digest_heading_level(tmp_path: Path) -> None:
    ...
    assert "<h2>Newsletter Briefings</h2>" in index_html
```

Add assertions that each issue renders a `View` link and optional short preview copy.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_newsletter_briefings_heading_matches_digest_heading_level -v`
Expected: FAIL because the current template uses `<h3>` and source-grouped rows.

**Step 3: Write minimal implementation**

Change the template to:
- use `<h2>` for `Newsletter Briefings`
- loop over sorted issues
- render one card per issue
- replace `View all` with `View`

Update CSS only as needed to keep the cards readable.

**Step 4: Run test to verify it passes**

Run the same command.
Expected: PASS

**Step 5: Commit**

```bash
git add templates/index.html static/style.css tests/test_site_generation.py
git commit -m "feat: redesign newsletter cards on home"
```

### Task 7: Update issue-page templates for article briefings

**Files:**
- Modify: `templates/newsletter_issue.html`
- Modify: `tests/test_site_generation.py`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

```python
def test_newsletter_issue_page_uses_article_briefing_blocks(tmp_path: Path) -> None:
    ...
    assert "요약" not in html
    assert 'href="https://example.com/a"' in html
    assert "한글 브리핑" in html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_newsletter_issue_page_uses_article_briefing_blocks -v`
Expected: FAIL because the old whole-issue summary block still renders.

**Step 3: Write minimal implementation**

Render each parsed article as a card with:
- linked English title
- Korean briefing text

Fallback to extracted `snippet` only if no Korean briefing exists.

**Step 4: Run test to verify it passes**

Run the same command.
Expected: PASS

**Step 5: Commit**

```bash
git add templates/newsletter_issue.html tests/test_site_generation.py
git commit -m "feat: render article briefings on newsletter pages"
```

### Task 8: Regenerate fixture data and verify preview output

**Files:**
- Modify: `data/newsletters/nature/*.json`
- Modify: `data/newsletters/science/*.json`
- Modify: `preview/**/*`

**Step 1: Re-run newsletter summary generation for local sample issues**

Run: `uv run python -m baiodigest.newsletters.fetch`

If live generation is too slow, update local sample issue JSON only after verifying the new schema.

**Step 2: Regenerate the preview**

Run: `BAIODIGEST_DOCS_DIR=preview uv run python -m baiodigest.main --generate-only`
Expected: preview files regenerate successfully.

**Step 3: Verify the preview manually**

Check:
- `preview/index.html`
- `preview/newsletters/nature/*.html`
- `preview/newsletters/science/*.html`

Confirm:
- one card per issue
- `Newsletter Briefings` heading matches `Today's Digest`
- article-level Korean briefings appear on issue pages

**Step 4: Run targeted tests**

Run: `uv run pytest tests/test_newsletter_models.py tests/test_newsletter_summarize.py tests/test_site_generation.py tests/test_main.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add data/newsletters preview src tests templates static
git commit -m "feat: redesign newsletter briefings experience"
```
