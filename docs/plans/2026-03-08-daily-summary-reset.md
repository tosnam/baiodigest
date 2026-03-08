# Daily Summary Reset Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 연구 레이더 변경을 제거하고, 기존 일간 논문 요약 페이지를 복원한 뒤 `왜 읽을 만한가`, `활용`, `주의`를 세로 블록으로 추가한다.

**Architecture:** 먼저 `8a368bd` 기준의 파일 상태를 복원해 연구 레이더 관련 모델/렌더링/주간 페이지를 제거한다. 그 다음 일간 페이지와 `Summary` 모델에 필요한 최소 필드만 다시 추가해, 기존 카드 레이아웃 위에 읽기 순서형 섹션을 얹는다.

**Tech Stack:** Python 3.12+, dataclasses, Jinja2, static HTML generation, custom CSS, pytest

---

### Task 1: Restore Pre-Radar Models and Generators

**Files:**
- Modify: `src/baiodigest/models.py`
- Modify: `src/baiodigest/filters/relevance.py`
- Modify: `src/baiodigest/summarizer/ollama.py`
- Modify: `src/baiodigest/summarizer/prompts.py`
- Modify: `src/baiodigest/generator/site.py`
- Modify: `templates/index.html`
- Modify: `templates/daily.html`
- Modify: `static/style.css`
- Test: `tests/test_models.py`
- Test: `tests/test_filters.py`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

연구 레이더 전용 출력이 더 이상 없어야 한다는 회귀 테스트를 추가한다.

```python
def test_generate_site_restores_pre_radar_home_without_weekly_preview(tmp_path) -> None:
    ...
    generator.generate()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")

    assert "최신 주간 요약" not in index_html
    assert "Research radar" not in index_html
    assert "기술 주제" not in index_html
```

모델 테스트도 추가해 `FilterResult`에서 레이더 필드가 제거되고, `Summary`는 `application_note`, `caution_note`만 유지하는지 고정한다.

```python
def test_daily_digest_json_round_trip_after_radar_reset() -> None:
    summary = Summary(
        background="배경",
        method="방법",
        result="결과",
        significance="의미",
        application_note="공정 적용 가능성",
        caution_note="추가 검증 필요",
    )
    result = FilterResult(
        relevant=True,
        confidence=0.91,
        category="protein_engineering",
        reason="산업적 활용 가치가 있다.",
        matched_keywords=["enzyme"],
    )
    ...
    assert loaded.entries[0].summary.application_note == "공정 적용 가능성"
    assert not hasattr(loaded.entries[0].filter_result, "topic_tags")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py::test_daily_digest_json_round_trip_after_radar_reset tests/test_site_generation.py::test_generate_site_restores_pre_radar_home_without_weekly_preview -v`

Expected: `FAIL` because the current code still exposes radar fields and weekly preview markup.

**Step 3: Write minimal implementation**

`8a368bd` 기준으로 아래 파일을 복원한 뒤, `Summary`에 `application_note`, `caution_note`만 다시 남긴다.

```bash
git restore --source=8a368bd -- \
  src/baiodigest/filters/relevance.py \
  src/baiodigest/summarizer/ollama.py \
  src/baiodigest/summarizer/prompts.py \
  src/baiodigest/generator/site.py \
  templates/index.html \
  templates/daily.html \
  static/style.css \
  tests/test_filters.py \
  tests/test_main.py \
  tests/test_site_generation.py
```

`src/baiodigest/models.py`는 수동으로 아래 형태로 맞춘다.

```python
@dataclass(slots=True)
class FilterResult:
    relevant: bool
    confidence: float
    category: str
    reason: str
    matched_keywords: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Summary:
    background: str
    method: str
    result: str
    significance: str
    application_note: str = ""
    caution_note: str = ""
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py::test_daily_digest_json_round_trip_after_radar_reset tests/test_site_generation.py::test_generate_site_restores_pre_radar_home_without_weekly_preview -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add src/baiodigest/models.py src/baiodigest/filters/relevance.py src/baiodigest/summarizer/ollama.py src/baiodigest/summarizer/prompts.py src/baiodigest/generator/site.py templates/index.html templates/daily.html static/style.css tests/test_models.py tests/test_filters.py tests/test_site_generation.py
git commit -m "refactor: remove research radar implementation"
```

### Task 2: Add Vertical Daily Summary Sections

**Files:**
- Modify: `templates/daily.html`
- Modify: `static/style.css`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

일간 페이지가 새 순서의 세로 블록을 렌더링하고 footer에서 reason이 제거되는지 검증한다.

```python
def test_generate_site_renders_daily_vertical_sections(tmp_path) -> None:
    ...
    daily_html = (docs_dir / "daily" / "2026-03-02.html").read_text(encoding="utf-8")

    assert "왜 읽을 만한가" in daily_html
    assert "배경" in daily_html
    assert "방법" in daily_html
    assert "결과" in daily_html
    assert "의미" in daily_html
    assert "활용" in daily_html
    assert "주의" in daily_html
    assert daily_html.index("왜 읽을 만한가") < daily_html.index("배경")
    assert "판정 근거:" not in daily_html
    assert "confidence: 0.80" in daily_html
```

스타일 테스트도 세로 스택 구조를 확인하도록 추가한다.

```python
def test_generate_site_copies_vertical_daily_section_styles(tmp_path) -> None:
    ...
    assert ".paper-detail-stack" in style_css
    assert ".paper-detail-block" in style_css
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py -k "vertical_daily_section" -v`

Expected: `FAIL` because the restored template does not yet render the new blocks.

**Step 3: Write minimal implementation**

`templates/daily.html`에서 기존 summary grid 아래에 세로 스택을 추가한다.

```html
<section class="paper-detail-stack">
  <section class="paper-detail-block">
    <h4>왜 읽을 만한가</h4>
    <p>{{ entry.filter_result.reason }}</p>
  </section>
  <section class="paper-detail-block">
    <h4>활용</h4>
    <p>{{ entry.summary.application_note or "구체적 활용 가능성은 원문에서 추가 확인이 필요합니다." }}</p>
  </section>
  <section class="paper-detail-block">
    <h4>주의</h4>
    <p>{{ entry.summary.caution_note or "해석 전 실험 조건과 검증 범위를 함께 확인하는 편이 좋습니다." }}</p>
  </section>
</section>
```

기존 4개 블록과 합쳐 최종 순서는 아래처럼 맞춘다.

```html
왜 읽을 만한가 → 배경 → 방법 → 결과 → 의미 → 활용 → 주의
```

footer는 아래처럼 단순화한다.

```html
<small>
  키워드: ...
  <br />
  confidence: {{ "%.2f"|format(entry.filter_result.confidence) }}
</small>
```

`static/style.css`에는 기존 `summary-block` 계열을 재사용하는 세로 스택 스타일을 추가한다.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_site_generation.py -k "vertical_daily_section" -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add templates/daily.html static/style.css tests/test_site_generation.py
git commit -m "feat: add vertical daily summary sections"
```

### Task 3: Regenerate Static Output and Verify Legacy Fallbacks

**Files:**
- Modify: `tests/test_site_generation.py`
- Verify Generated: `docs/index.html`
- Verify Generated: `docs/daily/*.html`
- Verify Removed: `docs/weekly/*`

**Step 1: Write the failing test**

레거시 데이터에서도 `활용`, `주의`가 기본 문장으로 렌더링되는지 확인한다.

```python
def test_generate_site_uses_default_daily_detail_copy_when_optional_fields_missing(tmp_path) -> None:
    ...
    daily_html = (docs_dir / "daily" / "2026-03-02.html").read_text(encoding="utf-8")

    assert "구체적 활용 가능성은 원문에서 추가 확인이 필요합니다." in daily_html
    assert "해석 전 실험 조건과 검증 범위를 함께 확인하는 편이 좋습니다." in daily_html
```

주간 산출물 제거도 확인한다.

```python
def test_generate_site_does_not_generate_weekly_pages(tmp_path) -> None:
    ...
    assert not (docs_dir / "weekly").exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py -k "default_daily_detail_copy or does_not_generate_weekly_pages" -v`

Expected: `FAIL` until fallback copy and weekly cleanup are complete.

**Step 3: Write minimal implementation**

생성기와 템플릿 기본값, 그리고 출력 디렉토리 정리를 마무리한다.

```python
def _cleanup_removed_output(docs_dir: Path) -> None:
    weekly_dir = docs_dir / "weekly"
    if weekly_dir.exists():
        shutil.rmtree(weekly_dir)
```

`generate()` 또는 관련 렌더링 경로에서 weekly 산출물을 지운다. 이후 실제 산출물을 재생성한다.

Run:

```bash
uv run python -m baiodigest.main --generate-only
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py tests/test_filters.py tests/test_site_generation.py tests/test_main.py -v`

Expected: `PASS`

추가 확인:

Run: `uv run python -m baiodigest.main --generate-only`

Expected: `docs/index.html`과 `docs/daily/*.html`가 새 구조로 생성되고 `docs/weekly/`는 존재하지 않는다.

**Step 5: Commit**

```bash
git add tests/test_site_generation.py docs/index.html docs/daily docs/static/style.css
git commit -m "docs: regenerate daily summary pages after radar reset"
```
