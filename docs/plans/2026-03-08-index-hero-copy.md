# Index Hero Copy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 홈 페이지의 히어로 제목을 `Today's Digest`로, CTA 문구를 `View`로 변경한다.

**Architecture:** 정적 사이트 생성 구조는 유지하고, 홈 템플릿의 문자열 두 개만 바꾼다. 생성 테스트의 기대값을 먼저 바꿔 실패를 확인한 뒤 템플릿을 수정하고 산출물을 재생성한다.

**Tech Stack:** Python, Jinja2, static HTML generation, pytest

---

### Task 1: Update Home Copy Expectations

**Files:**
- Modify: `tests/test_site_generation.py`

**Step 1: Write the failing test**

홈 생성 테스트가 새 문구를 기대하도록 수정한다.

```python
assert "Today's Digest" in index_html
assert ">View<" in index_html
assert "최신 다이제스트" not in index_html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_refresh_digest_home_layout -v`

Expected: `FAIL` because the template still renders the Korean copy.

**Step 3: Write minimal implementation**

No implementation in this task.

**Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_refresh_digest_home_layout -v`

Expected: `FAIL`

**Step 5: Commit**

Do not commit yet. Continue to Task 2.

### Task 2: Change Home Hero Copy

**Files:**
- Modify: `templates/index.html`
- Modify: `tests/test_site_generation.py`

**Step 1: Write minimal implementation**

`templates/index.html`에서 두 문구를 변경한다.

```html
<h2>Today's Digest</h2>
<p><a class="primary-link" href="{{ url_for('daily/' ~ latest.date ~ '.html') }}">View</a></p>
```

**Step 2: Run targeted tests**

Run: `uv run pytest tests/test_site_generation.py::test_generate_site_renders_refresh_digest_home_layout -v`

Expected: `PASS`

**Step 3: Commit**

```bash
git add templates/index.html tests/test_site_generation.py
git commit -m "feat: update index hero copy"
```

### Task 3: Regenerate Preview and Verify

**Files:**
- Verify Generated: `preview/index.html`

**Step 1: Regenerate preview**

Run:

```bash
env BAIODIGEST_DOCS_DIR=preview BAIODIGEST_SITE_PREFIX=/ uv run python -m baiodigest.main --generate-only
```

**Step 2: Run full verification**

Run: `uv run pytest`

Expected: `PASS`

**Step 3: Commit**

Do not commit `preview/`. Leave it untracked for local inspection.
