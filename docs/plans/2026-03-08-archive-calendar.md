# Archive Calendar Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 아카이브를 월별 캘린더 뷰로 전환하고, 월 네비게이션과 날짜별 논문 편수 표시를 제공한다.

**Architecture:** 기존 `StaticSiteGenerator` 데이터 흐름은 유지하되, 아카이브 전용 월 컨텍스트를 추가해 `/archive.html`과 `/archive/YYYY-MM.html`을 함께 생성한다. 캘린더는 일요일 시작 기준으로 계산하고, 템플릿은 단일 `archive.html`에서 월별 캘린더 페이지를 렌더링한다.

**Tech Stack:** Python 3.12+, Jinja2, static HTML generation, custom CSS, pytest

---

### Task 1: Add Archive Month Context and Monthly Page Generation

**Files:**
- Modify: `src/baiodigest/generator/site.py`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

월별 아카이브 페이지가 생성되고, `/archive.html`이 최신 월을 렌더링하는지 검증하는 테스트를 추가한다.

```python
def test_generate_site_renders_monthly_archive_pages(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digests(data_dir, ["2026-02-10", "2026-03-02", "2026-05-20"])

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    latest_archive = (docs_dir / "archive.html").read_text(encoding="utf-8")
    may_archive = (docs_dir / "archive" / "2026-05.html").read_text(encoding="utf-8")
    april_archive = (docs_dir / "archive" / "2026-04.html").read_text(encoding="utf-8")

    assert "2026년 5월" in latest_archive
    assert "2026년 5월" in may_archive
    assert "2026년 4월" in april_archive
    assert 'href="/baiodigest/archive/2026-04.html"' in may_archive
    assert 'href="/baiodigest/archive/2026-06.html"' not in may_archive
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_monthly_archive_pages -v`

Expected: `FAIL` because the generator only writes a single list-style `archive.html`.

**Step 3: Write minimal implementation**

`src/baiodigest/generator/site.py`에 월별 컨텍스트를 추가한다.

```python
@dataclass(slots=True, frozen=True)
class ArchiveDayCell:
    date: str
    day_number: int
    paper_count: int
    in_current_month: bool
    digest_url: str | None


@dataclass(slots=True, frozen=True)
class ArchiveMonthPage:
    year: int
    month: int
    title_label: str
    slug: str
    previous_month_url: str | None
    next_month_url: str | None
    weekday_labels: list[str]
    weeks: list[list[ArchiveDayCell]]
```

월 범위를 계산해 연속 월 리스트를 만들고, 각 월에 대해 `/archive/YYYY-MM.html`을 렌더링한다. 최신 월은 동일한 컨텍스트로 `/archive.html`도 함께 생성한다.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_monthly_archive_pages -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add src/baiodigest/generator/site.py tests/test_site_generation.py
git commit -m "feat: generate monthly archive calendar pages"
```

### Task 2: Render Sunday-First Monthly Calendar Template

**Files:**
- Modify: `templates/archive.html`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

캘린더 헤더, `0편` 표시, 데이터 있는 날짜 링크를 검증하는 테스트를 추가한다.

```python
def test_generate_site_renders_sunday_first_archive_calendar(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digests(data_dir, ["2026-03-02", "2026-03-07"])

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    archive_html = (docs_dir / "archive.html").read_text(encoding="utf-8")

    assert 'class="archive-calendar"' in archive_html
    assert "일" in archive_html
    assert "월" in archive_html
    assert "토" in archive_html
    assert "0편" in archive_html
    assert 'href="/baiodigest/daily/2026-03-02.html"' in archive_html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_sunday_first_archive_calendar -v`

Expected: `FAIL` because the current archive template is still a list layout.

**Step 3: Write minimal implementation**

`templates/archive.html`을 월 캘린더 템플릿으로 교체한다.

```html
<section class="archive-calendar">
  <div class="archive-calendar-header">
    <a href="{{ month_page.previous_month_url }}">이전 달</a>
    <div>
      <p class="eyebrow">Monthly archive</p>
      <h2>{{ month_page.title_label }}</h2>
    </div>
    <a href="{{ month_page.next_month_url }}">다음 달</a>
  </div>

  <div class="archive-weekdays">
    {% for label in month_page.weekday_labels %}
    <span>{{ label }}</span>
    {% endfor %}
  </div>

  <div class="archive-month-grid">
    {% for week in month_page.weeks %}
      {% for cell in week %}
      <article class="archive-day {{ 'is-active' if cell.digest_url else 'is-empty' }}">
        ...
      </article>
      {% endfor %}
    {% endfor %}
  </div>
</section>
```

활성 날짜는 일간 페이지 링크를 가지게 하고, 비활성 날짜는 `0편`만 보여준다.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_sunday_first_archive_calendar -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add templates/archive.html tests/test_site_generation.py
git commit -m "feat: render sunday-first archive calendar"
```

### Task 3: Add Calendar Styling and Full Verification

**Files:**
- Modify: `static/style.css`
- Test: `tests/test_site_generation.py`
- Verify Generated: `docs/archive.html`
- Verify Generated: `docs/archive/*.html`

**Step 1: Write the failing test**

아카이브 캘린더 전용 스타일 규칙이 복사된 CSS에 포함되는지 확인하는 테스트를 추가한다.

```python
def test_generate_site_copies_archive_calendar_styles(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = _repo_root() / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    _write_sample_digest(data_dir)

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    style_css = (docs_dir / "static" / "style.css").read_text(encoding="utf-8")

    assert ".archive-calendar" in style_css
    assert ".archive-month-grid" in style_css
    assert ".archive-day.is-empty" in style_css
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_copies_archive_calendar_styles -v`

Expected: `FAIL` because the current stylesheet has no calendar-specific rules.

**Step 3: Write minimal implementation**

`static/style.css`에 월 캘린더 스타일을 추가한다.

```css
.archive-calendar {
  padding: clamp(1.35rem, 2vw, 2rem);
  border: 1px solid var(--bd-border);
  border-radius: var(--bd-radius-lg);
  background: var(--bd-surface);
}

.archive-month-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.75rem;
}

.archive-day.is-empty {
  opacity: 0.7;
}
```

추가로 월 헤더, 요일 헤더, 활성 날짜 카드, 모바일 축약 스타일을 작성한다.

**Step 4: Run focused verification**

Run: `uv run pytest tests/test_site_generation.py -v`

Expected: all site-generation tests `PASS`

**Step 5: Regenerate site output**

Run: `uv run python -m baiodigest.main --generate-only`

Expected: `docs/archive.html`과 `docs/archive/*.html`이 갱신되고 런타임 오류가 없다.

**Step 6: Commit**

```bash
git add static/style.css tests/test_site_generation.py docs/archive.html docs/archive docs/static/style.css
git commit -m "feat: apply monthly archive calendar theme"
```
