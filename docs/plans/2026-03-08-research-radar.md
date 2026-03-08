# Research Radar Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 다이제스트를 산업 R&D용 연구 레이더로 확장해, 일간 페이지에서는 논문 선별을 돕고 주간 페이지에서는 변화 신호를 해석할 수 있게 만든다.

**Architecture:** 기존 `DailyDigest` 생성 흐름은 유지하되 `DigestEntry` 단위의 구조화 메타데이터를 추가하고, 정적 사이트 생성기에서 일간/주간 뷰를 각각 렌더링한다. 트렌드는 일간 페이지에서 억지로 만들지 않고, 사이트 생성 단계에서 최근 7일 집계를 계산해 별도 주간 페이지로 분리한다.

**Tech Stack:** Python 3.12+, dataclasses, Jinja2, static HTML generation, custom CSS, pytest

---

### Task 1: Extend Digest Models for Research Radar Metadata

**Files:**
- Modify: `src/baiodigest/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

`tests/test_models.py`에 구조화 메타데이터가 JSON round-trip 되는지 검증하는 테스트를 추가한다.

```python
def test_daily_digest_json_round_trip_with_research_radar_fields() -> None:
    summary = Summary(
        background="배경",
        method="방법",
        result="결과",
        significance="의미",
        why_it_matters="효소 최적화 후보를 빠르게 판단할 수 있다.",
        novelty_note="기존 대비 적은 실험으로 설계했다.",
        application_note="산업용 효소 스크리닝에 참고 가능하다.",
        caution_note="실제 공정 조건 검증은 추가로 필요하다.",
    )
    result = FilterResult(
        relevant=True,
        confidence=0.91,
        category="protein_engineering",
        reason="산업적 활용 가치가 있다.",
        matched_keywords=["protein engineering"],
        topic_tags=["ai_protein_design", "enzyme_stability"],
        problem_tags=["stability", "screening_speed"],
        research_type="method",
        practical_distance="mid_term",
    )

    digest = DailyDigest(...)
    loaded = DailyDigest.from_json(digest.to_json())

    assert loaded.entries[0].summary.why_it_matters == "효소 최적화 후보를 빠르게 판단할 수 있다."
    assert loaded.entries[0].filter_result.topic_tags == ["ai_protein_design", "enzyme_stability"]
    assert loaded.entries[0].filter_result.research_type == "method"
    assert loaded.entries[0].filter_result.practical_distance == "mid_term"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py::test_daily_digest_json_round_trip_with_research_radar_fields -v`

Expected: `FAIL` because `Summary` and `FilterResult` do not accept the new fields yet.

**Step 3: Write minimal implementation**

`src/baiodigest/models.py`에 새 필드를 추가하고, 기본값을 둬 과거 JSON과의 호환성을 유지한다.

```python
@dataclass(slots=True)
class FilterResult:
    relevant: bool
    confidence: float
    category: str
    reason: str
    matched_keywords: list[str] = field(default_factory=list)
    topic_tags: list[str] = field(default_factory=list)
    problem_tags: list[str] = field(default_factory=list)
    research_type: str = "basic"
    practical_distance: str = "foundational"


@dataclass(slots=True)
class Summary:
    background: str
    method: str
    result: str
    significance: str
    why_it_matters: str = ""
    novelty_note: str = ""
    application_note: str = ""
    caution_note: str = ""
```

`from_dict()`에서는 없는 키를 빈 문자열 또는 보수적인 기본값으로 채운다.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py::test_daily_digest_json_round_trip_with_research_radar_fields -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add tests/test_models.py src/baiodigest/models.py
git commit -m "feat: add research radar digest metadata"
```

### Task 2: Expand LLM Extraction and Relevance Classification

**Files:**
- Modify: `src/baiodigest/summarizer/prompts.py`
- Modify: `src/baiodigest/summarizer/ollama.py`
- Modify: `src/baiodigest/filters/relevance.py`
- Test: `tests/test_filters.py`

**Step 1: Write the failing test**

`tests/test_filters.py`에 LLM 응답에서 구조화 분류 필드가 반영되는지 검증하는 테스트를 추가한다.

```python
def test_llm_relevance_filter_preserves_research_radar_fields(settings, sample_paper) -> None:
    keyword_result = FilterResult(
        relevant=True,
        confidence=1.0,
        category="prefilter",
        reason="prefilter pass",
        matched_keywords=["enzyme"],
    )

    class FakeOllama:
        def classify_relevance(self, title: str, abstract: str):
            return RelevanceDecision(
                relevant=True,
                confidence=0.82,
                category="ai_enzyme",
                reason="산업적 활용 가능성이 있다.",
                topic_tags=["ai_protein_design"],
                problem_tags=["stability"],
                research_type="method",
                practical_distance="mid_term",
            )

    result = llm_relevance_filter(sample_paper, keyword_result, FakeOllama(), settings)

    assert result.topic_tags == ["ai_protein_design"]
    assert result.problem_tags == ["stability"]
    assert result.research_type == "method"
    assert result.practical_distance == "mid_term"
```

요약 프롬프트용 테스트도 함께 추가해 새 JSON 키가 파싱되는지 고정한다.

```python
def test_summarize_reads_research_radar_notes(monkeypatch, settings) -> None:
    client = OllamaClient(settings)
    monkeypatch.setattr(
        client,
        "_generate",
        lambda prompt: '{"background":"배경","method":"방법","result":"결과","significance":"의미","why_it_matters":"읽을 가치가 있다.","novelty_note":"새 방법이다.","application_note":"공정에 참고 가능하다.","caution_note":"스케일업 검증 필요"}',
    )

    summary = client.summarize("title", "abstract")

    assert summary.why_it_matters == "읽을 가치가 있다."
    assert summary.application_note == "공정에 참고 가능하다."
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_filters.py -k research_radar -v`

Expected: `FAIL` because `RelevanceDecision`, `FilterResult`, and `Summary` parsing do not expose the new fields.

**Step 3: Write minimal implementation**

`src/baiodigest/summarizer/prompts.py`에서 relevance/summarize 프롬프트의 JSON 스키마를 확장한다.

```python
- 키: relevant(boolean), confidence(0~1 float), category(string), reason(string)
+ 키: relevant(boolean), confidence(0~1 float), category(string), reason(string),
+     topic_tags(array), problem_tags(array), research_type(string), practical_distance(string)
```

```python
- 키: background, method, result, significance
+ 키: background, method, result, significance, why_it_matters,
+     novelty_note, application_note, caution_note
```

`src/baiodigest/summarizer/ollama.py`에서 파싱 모델을 확장한다.

```python
@dataclass(slots=True)
class RelevanceDecision:
    relevant: bool
    confidence: float
    category: str
    reason: str
    topic_tags: list[str]
    problem_tags: list[str]
    research_type: str
    practical_distance: str
```

`src/baiodigest/filters/relevance.py`는 새 필드를 `FilterResult`에 옮기고, 실패 시 보수적인 기본값을 채운다.

```python
return FilterResult(
    relevant=is_relevant,
    confidence=decision.confidence,
    category=decision.category,
    reason=korean_reason,
    matched_keywords=keyword_result.matched_keywords,
    topic_tags=decision.topic_tags or ["other"],
    problem_tags=decision.problem_tags or ["general_insight"],
    research_type=decision.research_type or "basic",
    practical_distance=decision.practical_distance or "foundational",
)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_filters.py -k research_radar -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add tests/test_filters.py src/baiodigest/summarizer/prompts.py src/baiodigest/summarizer/ollama.py src/baiodigest/filters/relevance.py
git commit -m "feat: extract research radar tags from llm"
```

### Task 3: Render a Research Radar Daily Digest

**Files:**
- Modify: `src/baiodigest/generator/site.py`
- Modify: `templates/daily.html`
- Modify: `static/style.css`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

`tests/test_site_generation.py`에 일간 페이지가 태그 그룹과 `why_it_matters`를 렌더링하는지 검증하는 테스트를 추가한다.

```python
def test_generate_site_renders_research_radar_daily_digest(tmp_path) -> None:
    entry = DigestEntry(
        paper=Paper(...),
        filter_result=FilterResult(
            relevant=True,
            confidence=0.9,
            category="ai_enzyme",
            reason="산업적 활용 가능성이 있다.",
            matched_keywords=["enzyme"],
            topic_tags=["ai_protein_design", "enzyme_stability"],
            problem_tags=["stability"],
            research_type="method",
            practical_distance="mid_term",
        ),
        summary=Summary(
            background="배경",
            method="방법",
            result="결과",
            significance="의미",
            why_it_matters="효소 최적화 아이디어를 바로 얻을 수 있다.",
            novelty_note="데이터 효율이 높다.",
            application_note="효소 라이브러리 설계에 적용 가능하다.",
            caution_note="실험 검증 범위는 제한적이다.",
        ),
    )

    ...
    daily_html = (docs_dir / "daily" / "2026-03-02.html").read_text(encoding="utf-8")

    assert "왜 읽을 만한가" in daily_html
    assert "효소 최적화 아이디어를 바로 얻을 수 있다." in daily_html
    assert 'class="topic-chip"' in daily_html
    assert 'class="problem-chip"' in daily_html
    assert "연구 성격" in daily_html
    assert "실무 근접도" in daily_html
    assert 'class="daily-topic-group"' in daily_html
```

CSS 복사 테스트도 함께 추가한다.

```python
def test_generate_site_copies_research_radar_daily_styles(tmp_path) -> None:
    ...
    assert ".daily-topic-group" in style_css
    assert ".topic-chip" in style_css
    assert ".paper-radar-grid" in style_css
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py -k research_radar_daily -v`

Expected: `FAIL` because the current daily template only renders summary blocks and footer notes.

**Step 3: Write minimal implementation**

`src/baiodigest/generator/site.py`에 일간 페이지용 뷰 모델을 추가한다.

```python
@dataclass(slots=True, frozen=True)
class DailyTopicGroup:
    name: str
    entries: list[DigestEntry]


def _group_entries_by_topic(digest: DailyDigest) -> list[DailyTopicGroup]:
    ...
```

`templates/daily.html`은 선별형 레이아웃으로 바꾼다.

```html
<section class="daily-radar-summary">
  <h3>오늘의 연구 지도</h3>
  <p>기술 주제 {{ digest_topic_count }}개, 문제 유형 {{ digest_problem_count }}개</p>
</section>

{% for group in topic_groups %}
<section class="daily-topic-group">
  <header class="daily-topic-header">
    <h3>{{ group.name }}</h3>
    <p>{{ group.entries|length }}편</p>
  </header>
  {% for entry in group.entries %}
  <article class="paper-card">
    <section class="paper-radar-grid">
      <div>
        <h4>왜 읽을 만한가</h4>
        <p>{{ entry.summary.why_it_matters }}</p>
      </div>
      <div>
        <h4>연구 성격</h4>
        <p>{{ entry.filter_result.research_type }}</p>
      </div>
      <div>
        <h4>실무 근접도</h4>
        <p>{{ entry.filter_result.practical_distance }}</p>
      </div>
    </section>
  </article>
  {% endfor %}
</section>
{% endfor %}
```

`static/style.css`에는 태그 칩, 그룹 헤더, 메타 그리드 스타일을 추가한다.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_site_generation.py -k research_radar_daily -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add tests/test_site_generation.py src/baiodigest/generator/site.py templates/daily.html static/style.css
git commit -m "feat: render research radar daily digest"
```

### Task 4: Generate Weekly Signal Pages

**Files:**
- Modify: `src/baiodigest/generator/site.py`
- Create: `templates/weekly.html`
- Modify: `templates/index.html`
- Modify: `static/style.css`
- Test: `tests/test_site_generation.py`

**Step 1: Write the failing test**

`tests/test_site_generation.py`에 주간 페이지 생성과 홈 진입 링크를 검증하는 테스트를 추가한다.

```python
def test_generate_site_renders_weekly_signal_pages(tmp_path) -> None:
    _write_digest(
        data_dir,
        "2026-03-03",
        topic_tags=["ai_protein_design"],
        problem_tags=["stability"],
    )
    _write_digest(
        data_dir,
        "2026-03-05",
        topic_tags=["ai_protein_design"],
        problem_tags=["stability"],
    )
    _write_digest(
        data_dir,
        "2026-03-07",
        topic_tags=["host_engineering"],
        problem_tags=["yield"],
    )

    generator.generate()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")
    weekly_html = (docs_dir / "weekly" / "2026-W10.html").read_text(encoding="utf-8")

    assert "최신 주간 요약" in index_html
    assert 'href="/baiodigest/weekly/2026-W10.html"' in index_html
    assert "이번 주 변화 신호" in weekly_html
    assert "ai_protein_design" in weekly_html
    assert "host_engineering" in weekly_html
```

변화가 적을 때 정직한 상태 메시지를 보장하는 테스트도 추가한다.

```python
def test_generate_site_renders_weekly_no_signal_message(tmp_path) -> None:
    ...
    assert "뚜렷한 신규 흐름보다 기존 주제의 연속선상 연구가 중심입니다." in weekly_html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py -k weekly_signal -v`

Expected: `FAIL` because no weekly pages or weekly navigation exist.

**Step 3: Write minimal implementation**

`src/baiodigest/generator/site.py`에 주간 컨텍스트를 추가한다.

```python
@dataclass(slots=True, frozen=True)
class WeeklySignal:
    label: str
    count: int
    representative_dates: list[str]


@dataclass(slots=True, frozen=True)
class WeeklyPage:
    slug: str
    title_label: str
    signals: list[WeeklySignal]
    has_meaningful_change: bool
```

최근 7일 단위로 digests를 묶고 topic/problem tag 빈도를 집계한다. 변화가 충분하지 않으면 `signals=[]`와 상태 메시지를 렌더링한다.

`templates/weekly.html`은 신호 카드와 대표 논문 링크를 가진 정적 페이지를 렌더링한다.

```html
<section class="weekly-hero">
  <p class="eyebrow">Weekly signal</p>
  <h2>{{ weekly_page.title_label }}</h2>
</section>

{% if weekly_page.has_meaningful_change %}
  {% for signal in weekly_page.signals %}
  <article class="weekly-signal-card">...</article>
  {% endfor %}
{% else %}
  <p class="weekly-empty-state">뚜렷한 신규 흐름보다 기존 주제의 연속선상 연구가 중심입니다.</p>
{% endif %}
```

`templates/index.html`은 최신 일간 링크 옆에 최신 주간 요약 링크를 추가한다.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_site_generation.py -k weekly_signal -v`

Expected: `PASS`

**Step 5: Commit**

```bash
git add tests/test_site_generation.py src/baiodigest/generator/site.py templates/weekly.html templates/index.html static/style.css
git commit -m "feat: add weekly signal digest pages"
```

### Task 5: Verify End-to-End Generation and Preserve Backward Compatibility

**Files:**
- Modify: `tests/test_site_generation.py`
- Modify: `tests/test_main.py`
- Verify Generated: `docs/index.html`
- Verify Generated: `docs/daily/*.html`
- Verify Generated: `docs/weekly/*.html`

**Step 1: Write the failing test**

기존 구조의 최소 JSON만 있어도 사이트 생성이 실패하지 않는지 검증하는 회귀 테스트를 추가한다.

```python
def test_generate_site_supports_legacy_digest_without_radar_fields(tmp_path) -> None:
    digest = DailyDigest(
        date="2026-03-02",
        entries=[
            DigestEntry(
                paper=Paper(...),
                filter_result=FilterResult(
                    relevant=True,
                    confidence=0.8,
                    category="ai_enzyme",
                    reason="산업적 활용 가능성이 있다.",
                ),
                summary=Summary(
                    background="배경",
                    method="방법",
                    result="결과",
                    significance="의미",
                ),
            )
        ],
        stats={"summarized": 1},
    )

    ...
    generator.generate()

    daily_html = (docs_dir / "daily" / "2026-03-02.html").read_text(encoding="utf-8")
    assert "왜 읽을 만한가" in daily_html
```

파이프라인 수준 테스트도 추가해 `main.py`가 새 필드가 있는 요약과 분류를 저장하는지 검증한다.

```python
def test_run_pipeline_writes_research_radar_fields(...):
    ...
    digest = DailyDigest.from_file(data_dir / "2026-03-08.json")
    assert digest.entries[0].summary.why_it_matters == "읽을 가치가 있다."
    assert digest.entries[0].filter_result.topic_tags == ["ai_protein_design"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_supports_legacy_digest_without_radar_fields tests/test_main.py::test_run_pipeline_writes_research_radar_fields -v`

Expected: at least one `FAIL` until the fallback rendering and pipeline persistence are complete.

**Step 3: Write minimal implementation**

호환성 보정과 렌더링 기본값을 마무리한다.

```python
def _display_why_it_matters(entry: DigestEntry) -> str:
    if entry.summary.why_it_matters.strip():
        return entry.summary.why_it_matters
    return entry.filter_result.reason
```

주간 생성은 데이터가 없을 때 `weekly/`를 비우고, 홈은 주간 페이지가 없는 경우 링크를 숨긴다. `main.py`는 기존 루프를 유지하면서 확장된 `Summary`와 `FilterResult`를 그대로 직렬화한다.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py tests/test_filters.py tests/test_site_generation.py tests/test_main.py -v`

Expected: `PASS`

추가 확인:

Run: `uv run python -m baiodigest.main --generate-only`

Expected: `docs/index.html`, `docs/daily/*.html`, `docs/weekly/*.html` regenerated without errors.

**Step 5: Commit**

```bash
git add tests/test_site_generation.py tests/test_main.py src/baiodigest/generator/site.py src/baiodigest/main.py templates/index.html templates/daily.html templates/weekly.html static/style.css
git commit -m "feat: complete research radar site generation"
```
