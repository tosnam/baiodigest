# Repo Hygiene And README Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `CLAUDE.md`, `docs/plans/`, `tasks/`를 저장소 추적 대상에서 제거하고, `README.md`를 현재 서비스 상태와 맞게 갱신한다.

**Architecture:** git ignore 정책과 git index 상태를 함께 정리해야 하므로, `.gitignore` 수정과 `git rm --cached`를 같은 작업으로 묶는다. `README.md`는 실제 코드와 템플릿 상태를 기준으로 최소 수정하고, 변경 후 테스트와 원격 푸시까지 마무리한다.

**Tech Stack:** Git, Python, pytest, Markdown

---

### Task 1: Ignore Local Planning Files

**Files:**
- Modify: `.gitignore`

**Step 1: Update ignore rules**

`.gitignore`에 아래 경로를 추가한다.

```gitignore
CLAUDE.md
docs/plans/
tasks/
```

**Step 2: Verify ignore behavior**

Run: `git check-ignore -v CLAUDE.md docs/plans tasks`

Expected: each path is reported as ignored by `.gitignore`.

**Step 3: Commit**

Do not commit yet. Continue to Task 2.

### Task 2: Remove Tracked Local Files From Git Index

**Files:**
- Remove from index: `CLAUDE.md`
- Remove from index: `docs/plans/*`
- Remove from index: `tasks/*`

**Step 1: Untrack existing files**

Run:

```bash
git rm --cached CLAUDE.md
git rm -r --cached docs/plans
git rm -r --cached tasks
```

**Step 2: Verify staged removals**

Run: `git status --short`

Expected: `.gitignore` modified and target files staged as deletions from git only.

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore local planning files"
```

### Task 3: Refresh README

**Files:**
- Modify: `README.md`

**Step 1: Update project description**

Adjust the README to match current behavior:

- remove `Pico CSS` wording
- describe the daily page as `왜 읽을 만한가 / 배경 / 방법 / 결과 / 활용`
- keep existing CLI and notification flow only where it matches current code

**Step 2: Review diff**

Run: `git diff -- README.md`

Expected: only documentation text changes, no unrelated edits.

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: refresh readme"
```

### Task 4: Verify And Publish

**Files:**
- Verify: repository root

**Step 1: Run tests**

Run: `uv run pytest`

Expected: `PASS`

**Step 2: Merge to main and verify**

Run on repository root:

```bash
git merge --no-ff feat/repo-hygiene-readme
uv run pytest
```

Expected: merged branch still passes tests.

**Step 3: Push**

Run:

```bash
git push origin main
```

Expected: remote `main` updated successfully.
