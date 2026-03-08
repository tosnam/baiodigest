# Digest Web Design Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 가독성을 우선한 차분한 미니멀 톤으로 다이제스트 정적 웹 페이지를 재설계한다.

**Architecture:** `StaticSiteGenerator`의 데이터 흐름은 유지하고, 변경은 Jinja 템플릿과 사이트 전용 CSS에 집중한다. 테스트는 렌더링된 HTML과 복사된 정적 CSS를 직접 검사해 새 정보 구조와 한글 중심 타이포 설정이 실제 출력에 반영되는지 확인한다.

**Tech Stack:** Python 3.12, Jinja2, Pico CSS, custom CSS, pytest

---

### Task 1: Shared Shell, Home, Archive Markup

**Files:**
- Modify: `templates/base.html`
- Modify: `templates/index.html`
- Modify: `templates/archive.html`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

`tests/test_site_generation.py`에 홈과 아카이브의 새 정보 구조를 검증하는 테스트를 추가한다.

```python
def test_generate_site_renders_redesigned_index_and_archive(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digest(data_dir)

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")
    archive_html = (docs_dir / "archive.html").read_text(encoding="utf-8")

    assert 'class="site-shell"' in index_html
    assert 'class="hero-summary"' in index_html
    assert "최신 다이제스트" in index_html
    assert 'class="digest-list"' in index_html
    assert 'class="archive-list"' in archive_html
    assert 'class="archive-row"' in archive_html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_redesigned_index_and_archive -v`

Expected: `FAIL` because the current templates do not render the new classes or sections.

**Step 3: Write minimal implementation**

`templates/base.html`에 사이트 래퍼와 폰트 로드, 단순한 헤더 구조를 추가한다.

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@500;700&display=swap"
  rel="stylesheet"
/>
<body>
  <div class="site-shell">
    <header class="site-header">...</header>
    <main class="site-main container">
      {% block content %}{% endblock %}
    </main>
  </div>
</body>
```

`templates/index.html`은 최신 다이제스트 카드와 최근 기록 리스트 구조로 바꾼다.

```html
<section class="hero-summary">
  <p class="eyebrow">Bio industry research digest</p>
  <h2>최신 다이제스트</h2>
  <p class="hero-copy">...</p>
  <a class="primary-link" href="{{ url_for('daily/' ~ latest.date ~ '.html') }}">
    {{ latest.date }} 다이제스트 보기
  </a>
</section>

<section class="digest-list">...</section>
```

`templates/archive.html`은 표 대신 리스트형 구조로 바꾼다.

```html
<section class="archive-list">
  {% for digest in digests %}
  <article class="archive-row">
    <div>
      <h3>{{ digest.date }}</h3>
      <p>논문 {{ digest.entries|length }}편</p>
    </div>
    <a href="{{ url_for('daily/' ~ digest.date ~ '.html') }}">열기</a>
  </article>
  {% endfor %}
</section>
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_redesigned_index_and_archive -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add tests/test_site_generation.py templates/base.html templates/index.html templates/archive.html
git commit -m "feat: redesign digest home and archive layout"
```

### Task 2: Daily Digest Card Layout

**Files:**
- Modify: `templates/daily.html`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

일간 상세 페이지의 헤더, 논문 카드, 메타 영역을 검증하는 테스트를 추가한다.

```python
def test_generate_site_renders_redesigned_daily_digest(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")

    entry = DigestEntry(
        paper=Paper(
            title="Test paper",
            abstract="Test abstract",
            authors=["A"],
            affiliations=["Example Institute"],
            doi=None,
            source="pubmed",
            source_type="published",
            journal="Test Journal",
            url="https://example.org",
            category=None,
            date="2026-03-02",
            mesh_terms=[],
        ),
        filter_result=FilterResult(
            relevant=True,
            confidence=0.8,
            category="ai_enzyme",
            reason="산업적 활용 가능성이 있어 관련 논문으로 판단했습니다.",
            matched_keywords=["enzyme"],
        ),
        summary=Summary(
            background="배경",
            method="방법",
            result="결과",
            significance="의미",
        ),
    )
    DailyDigest(date="2026-03-02", entries=[entry], stats={"collected": 1, "summarized": 1}).to_file(
        data_dir / "2026-03-02.json"
    )

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    daily_html = (docs_dir / "daily" / "2026-03-02.html").read_text(encoding="utf-8")

    assert 'class="digest-header"' in daily_html
    assert 'class="paper-card"' in daily_html
    assert 'class="paper-meta"' in daily_html
    assert 'class="summary-grid"' in daily_html
    assert 'class="paper-notes"' in daily_html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_redesigned_daily_digest -v`

Expected: `FAIL` because the current daily template renders a plain article stack.

**Step 3: Write minimal implementation**

`templates/daily.html`을 읽기 흐름 중심 구조로 바꾼다.

```html
<section class="digest-header">
  <p class="eyebrow">Daily digest</p>
  <h2>{{ digest.date }}</h2>
  <p>총 {{ digest.entries|length }}편의 논문을 정리했습니다.</p>
</section>

{% for entry in digest.entries %}
<article class="paper-card">
  <header class="paper-meta">
    <h3><a href="{{ entry.paper.url }}" target="_blank" rel="noopener noreferrer">{{ entry.paper.title }}</a></h3>
    <p>{{ entry.paper.journal or "Unknown journal" }}</p>
    {% if entry.paper.affiliations %}
    <p>{{ entry.paper.affiliations[-1] }}</p>
    {% endif %}
  </header>

  <section class="summary-grid">
    <div class="summary-block">...</div>
    <div class="summary-block">...</div>
    <div class="summary-block">...</div>
    <div class="summary-block">...</div>
  </section>

  <footer class="paper-notes">...</footer>
</article>
{% endfor %}
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_redesigned_daily_digest -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add tests/test_site_generation.py templates/daily.html
git commit -m "feat: redesign daily digest article layout"
```

### Task 3: Theme Stylesheet for Korean-First Readability

**Files:**
- Modify: `static/style.css`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

복사된 정적 CSS에 새 타이포와 주요 컴포넌트 스타일이 포함되는지 검증하는 테스트를 추가한다.

```python
def test_generate_site_copies_digest_theme_styles(tmp_path) -> None:
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

    assert "Noto Sans KR" in style_css
    assert "Noto Serif KR" in style_css
    assert ".hero-summary" in style_css
    assert ".paper-card" in style_css
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_copies_digest_theme_styles -v`

Expected: `FAIL` because the current stylesheet does not define the new font stack or component selectors.

**Step 3: Write minimal implementation**

`static/style.css`를 색상 변수, 타이포, 레이아웃, 카드, 메타 영역 중심으로 재구성한다.

```css
:root {
  --bd-bg: #f7f4ee;
  --bd-surface: #fffdf9;
  --bd-border: #d8d4ca;
  --bd-ink: #1d2428;
  --bd-muted: #5d6a70;
  --bd-accent: #506c74;
  --bd-sans: "Noto Sans KR", sans-serif;
  --bd-serif: "Noto Serif KR", serif;
}

body {
  background: linear-gradient(180deg, #fbf8f2 0%, #f3efe7 100%);
  color: var(--bd-ink);
  font-family: var(--bd-sans);
  line-height: 1.75;
}

.hero-summary,
.archive-row,
.paper-card {
  background: var(--bd-surface);
  border: 1px solid var(--bd-border);
  border-radius: 1.25rem;
}
```

추가로 `.site-shell`, `.site-main`, `.eyebrow`, `.digest-list`, `.archive-list`, `.digest-header`, `.paper-meta`, `.summary-grid`, `.summary-block`, `.paper-notes`에 대한 규칙을 작성한다.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_copies_digest_theme_styles -v`

Expected: `PASS`

**Step 5: Run the focused suite**

Run: `uv run pytest tests/test_site_generation.py -v`

Expected: all site-generation tests `PASS`

**Step 6: Regenerate the site for manual verification**

Run: `uv run python -m baiodigest.main --generate-only`

Expected: updated files under `docs/` with no runtime errors.

**Step 7: Commit**

```bash
git add tests/test_site_generation.py static/style.css docs/index.html docs/archive.html docs/daily
git commit -m "feat: apply calm minimalist digest theme"
```
