# Daily Summary Simplify Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 일간 논문 요약 카드에서 `활용`, `주의` 추가 블록을 제거하고, 기존 `의미`를 `활용`으로 재라벨링한다.

**Architecture:** 현재 세로 카드 레이아웃은 유지하되, `Summary.significance`를 보여주는 마지막 블록의 제목만 `활용`으로 바꾼다. 더 이상 쓰지 않는 `Summary.application_note`, `Summary.caution_note`와 summary 생성/파싱 로직은 함께 제거해 모델과 UI를 다시 일치시킨다.

**Tech Stack:** Python 3.12+, dataclasses, Jinja2, static HTML generation, custom CSS, pytest

---

### Task 1: Remove Unused Summary Fields

**Files:**
- Modify: `src/baiodigest/models.py`
- Modify: `src/baiodigest/summarizer/prompts.py`
- Modify: `src/baiodigest/summarizer/ollama.py`
- Test: `tests/test_models.py`
- Test: `tests/test_filters.py`

**Step 1: Write the failing test**

`Summary`에서 `application_note`, `caution_note`가 제거되는지 고정한다.

```python
def test_daily_digest_json_round_trip_without_optional_summary_notes() -> None:
    summary = Summary(
        background="배경",
        method="방법",
        result="결과",
        significance="의미",
    )
    ...
    loaded = DailyDigest.from_json(digest.to_json())
    assert loaded.entries[0].summary.significance == "의미"
    assert not hasattr(loaded.entries[0].summary, "application_note")
    assert not hasattr(loaded.entries[0].summary, "caution_note")
```

요약 파서 테스트도 다시 단순화한다.

```python
def test_summarize_reads_core_summary_fields_only() -> None:
    ...
    summary = client.summarize("title", "abstract")
    assert summary.background == "배경"
    assert summary.significance == "의미"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py::test_daily_digest_json_round_trip_without_optional_summary_notes tests/test_filters.py::test_summarize_reads_core_summary_fields_only -v`

Expected: `FAIL` because the current model and parser still expose `application_note`, `caution_note`.

**Step 3: Write minimal implementation**

`src/baiodigest/models.py`에서 `Summary`를 다시 4필드로 축소한다.

```python
@dataclass(slots=True)
class Summary:
    background: str
    method: str
    result: str
    significance: str
```

`src/baiodigest/summarizer/prompts.py`의 summary 키 목록도 `background, method, result, significance`로 줄인다. `src/baiodigest/summarizer/ollama.py`는 4개 키만 파싱한다.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py::test_daily_digest_json_round_trip_without_optional_summary_notes tests/test_filters.py::test_summarize_reads_core_summary_fields_only -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add src/baiodigest/models.py src/baiodigest/summarizer/prompts.py src/baiodigest/summarizer/ollama.py tests/test_models.py tests/test_filters.py
git commit -m "refactor: remove unused daily summary note fields"
```

### Task 2: Simplify Daily Card Copy

**Files:**
- Modify: `templates/daily.html`
- Modify: `tests/test_site_generation.py`

**Step 1: Write the failing test**

일간 카드가 5개 블록만 렌더링하고 마지막 제목이 `활용`인지 검증한다.

```python
def test_generate_site_renders_simplified_daily_sections(tmp_path) -> None:
    ...
    headings = [
        "<h4>왜 읽을 만한가</h4>",
        "<h4>배경</h4>",
        "<h4>방법</h4>",
        "<h4>결과</h4>",
        "<h4>활용</h4>",
    ]
    positions = [daily_html.index(heading) for heading in headings]
    assert positions == sorted(positions)
    assert "<h4>의미</h4>" not in daily_html
    assert "<h4>주의</h4>" not in daily_html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_simplified_daily_sections -v`

Expected: `FAIL` because the current template still renders separate `활용`, `주의` blocks.

**Step 3: Write minimal implementation**

`templates/daily.html`에서 마지막 세 블록을 아래처럼 정리한다.

```html
<section class="paper-detail-block">
  <h4>활용</h4>
  <p>{{ entry.summary.significance }}</p>
</section>
```

즉, 기존 `의미` 제목을 `활용`으로 바꾸고 별도 `활용`, `주의` 블록은 제거한다.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_simplified_daily_sections -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add templates/daily.html tests/test_site_generation.py
git commit -m "feat: simplify daily summary sections"
```

### Task 3: Regenerate Preview and Docs

**Files:**
- Verify Generated: `docs/index.html`
- Verify Generated: `docs/daily/*.html`
- Verify Generated: `preview/index.html`
- Verify Generated: `preview/daily/*.html`

**Step 1: Write the failing test**

정적 산출물 회귀 테스트를 보강한다.

```python
def test_generate_site_output_uses_simplified_daily_sections(tmp_path) -> None:
    ...
    assert "<h4>활용</h4>" in daily_html
    assert "<h4>의미</h4>" not in daily_html
    assert "<h4>주의</h4>" not in daily_html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_output_uses_simplified_daily_sections -v`

Expected: `FAIL` until template and generator output are regenerated.

**Step 3: Write minimal implementation**

산출물을 다시 생성한다.

Run:

```bash
uv run python -m baiodigest.main --generate-only
env BAIODIGEST_DOCS_DIR=preview BAIODIGEST_SITE_PREFIX=/ uv run python -m baiodigest.main --generate-only
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py tests/test_filters.py tests/test_site_generation.py tests/test_main.py -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add docs/index.html docs/daily docs/static/style.css preview
git commit -m "docs: regenerate simplified daily summary pages"
```
