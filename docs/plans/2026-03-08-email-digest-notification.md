# Email Digest Notification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 일일 다이제스트가 배포된 뒤 Gmail SMTP로 등록된 수신자 목록에 게시 알림 메일을 발송한다.

**Architecture:** 메일 발송 로직은 새 Python 알림 모듈과 CLI로 분리하고, 기존 `scripts/run-daily.sh`는 `git push` 성공 이후에만 해당 CLI를 호출한다. 설정과 수신자 목록은 `config.py`와 TOML 파일 로더에서 관리하고, 메일 내용은 다이제스트 JSON과 사이트 URL을 바탕으로 plain text로 생성한다.

**Tech Stack:** Python 3.12+, stdlib `smtplib`/`email`, TOML(`tomllib`), pytest, bash

---

### Task 1: Add SMTP and recipient configuration loading

**Files:**
- Modify: `src/baiodigest/config.py`
- Modify: `.gitignore`
- Create: `recipients.toml.example`
- Test: `tests/test_config.py`

**Step 1: Write the failing test**

Add tests covering:

```python
def test_recipients_loaded_from_env_override(monkeypatch, tmp_path: Path) -> None:
    recipients_file = tmp_path / "recipients.toml"
    recipients_file.write_text(
        """
[[recipients]]
email = "reader@example.com"
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("BAIODIGEST_RECIPIENTS_FILE", str(recipients_file))

    settings = Settings()

    assert settings.recipients_file == recipients_file
    assert len(settings.email_recipients) == 1
    assert settings.email_recipients[0].email == "reader@example.com"


def test_smtp_defaults(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BAIODIGEST_RECIPIENTS_FILE", str(tmp_path / "recipients.toml"))
    (tmp_path / "recipients.toml").write_text("[[recipients]]\nemail='reader@example.com'\n", encoding="utf-8")

    settings = Settings()

    assert settings.smtp_host == "smtp.gmail.com"
    assert settings.smtp_port == 465
    assert settings.smtp_from_name == "baioDigest"


def test_recipients_validation_failure_for_empty_list(monkeypatch, tmp_path: Path) -> None:
    recipients_file = tmp_path / "recipients.toml"
    recipients_file.write_text("recipients = []\n", encoding="utf-8")
    monkeypatch.setenv("BAIODIGEST_RECIPIENTS_FILE", str(recipients_file))

    with pytest.raises(ValueError):
        Settings()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL because `Settings` does not yet expose SMTP or recipient fields.

**Step 3: Write minimal implementation**

Update `src/baiodigest/config.py`:

```python
@dataclass(slots=True, frozen=True)
class EmailRecipient:
    email: str


def _load_recipients(path: Path) -> list[EmailRecipient]:
    ...


@dataclass(slots=True)
class Settings:
    smtp_host: str = field(default_factory=lambda: os.getenv("BAIODIGEST_SMTP_HOST", "smtp.gmail.com"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("BAIODIGEST_SMTP_PORT", "465")))
    smtp_username: str = field(default_factory=lambda: os.getenv("BAIODIGEST_SMTP_USERNAME", ""))
    smtp_app_password: str = field(default_factory=lambda: os.getenv("BAIODIGEST_SMTP_APP_PASSWORD", ""))
    smtp_from_name: str = field(default_factory=lambda: os.getenv("BAIODIGEST_SMTP_FROM_NAME", "baioDigest"))
    recipients_file: Path = field(default_factory=lambda: _resolve_path("BAIODIGEST_RECIPIENTS_FILE", "recipients.toml"))
    site_url: str = field(default_factory=lambda: os.getenv("BAIODIGEST_SITE_URL", "").rstrip("/"))
    email_recipients: list[EmailRecipient] = field(init=False)

    def __post_init__(self) -> None:
        self.pubmed_queries = _load_pubmed_queries(self.queries_file)
        self.email_recipients = _load_recipients(self.recipients_file)
```

Add `recipients.toml.example`:

```toml
[[recipients]]
email = "reader@example.com"
```

Update `.gitignore` to ignore `recipients.toml` and optional `.env`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/config.py tests/test_config.py .gitignore recipients.toml.example
git commit -m "feat: add email notification settings"
```

### Task 2: Add email message builder and SMTP sender

**Files:**
- Create: `src/baiodigest/notifications/__init__.py`
- Create: `src/baiodigest/notifications/email.py`
- Test: `tests/test_notify.py`

**Step 1: Write the failing test**

Create `tests/test_notify.py` with focused unit tests:

```python
from baiodigest.config import EmailRecipient
from baiodigest.notifications.email import build_digest_email, send_digest_email


def test_build_digest_email_includes_digest_links() -> None:
    subject, body = build_digest_email(
        digest_date="2026-03-08",
        entry_count=2,
        site_url="https://example.github.io/baiodigest",
    )

    assert subject == "[baioDigest] 2026-03-08 digest is live"
    assert "2026-03-08" in body
    assert "2 papers" in body
    assert "https://example.github.io/baiodigest/index.html" in body
    assert "https://example.github.io/baiodigest/daily/2026-03-08.html" in body


def test_send_digest_email_uses_smtp_ssl(monkeypatch) -> None:
    sent = {}

    class FakeSMTP:
        def __init__(self, host: str, port: int) -> None:
            sent["host"] = host
            sent["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def login(self, username: str, password: str) -> None:
            sent["login"] = (username, password)

        def send_message(self, message) -> None:
            sent["message"] = message

    monkeypatch.setattr("baiodigest.notifications.email.smtplib.SMTP_SSL", FakeSMTP)

    send_digest_email(...)

    assert sent["host"] == "smtp.gmail.com"
    assert sent["login"] == ("sender@example.com", "app-password")
    assert sent["message"]["To"] == "reader1@example.com, reader2@example.com"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_notify.py -v`
Expected: FAIL because the notification module does not exist yet.

**Step 3: Write minimal implementation**

Create `src/baiodigest/notifications/email.py`:

```python
def build_digest_email(digest_date: str, entry_count: int, site_url: str) -> tuple[str, str]:
    subject = f"[baioDigest] {digest_date} digest is live"
    body = "\n".join(
        [
            f"Today's digest for {digest_date} is live.",
            f"Included papers: {entry_count}",
            "",
            f"Home: {site_url}/index.html",
            f"Daily: {site_url}/daily/{digest_date}.html",
        ]
    )
    return subject, body


def send_digest_email(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_app_password: str,
    from_name: str,
    recipients: list[EmailRecipient],
    subject: str,
    body: str,
) -> None:
    ...
```

Use `EmailMessage`, `set_content(body)`, `SMTP_SSL`, `login`, and `send_message`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_notify.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/notifications/__init__.py src/baiodigest/notifications/email.py tests/test_notify.py
git commit -m "feat: add digest email sender"
```

### Task 3: Add notification CLI for a published digest

**Files:**
- Create: `src/baiodigest/notify.py`
- Modify: `tests/test_notify.py`
- Reuse: `src/baiodigest/models.py`

**Step 1: Write the failing test**

Extend `tests/test_notify.py` with CLI-oriented tests:

```python
from baiodigest.notify import notify_for_date
from baiodigest.models import DailyDigest


def test_notify_for_date_reads_digest_and_sends_email(monkeypatch, tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    digest = DailyDigest(date="2026-03-08", entries=[], stats={"summarized": 2})
    digest.to_file(data_dir / "2026-03-08.json")
    (docs_dir / "daily").mkdir(parents=True)
    (docs_dir / "daily" / "2026-03-08.html").write_text("<html></html>", encoding="utf-8")

    monkeypatch.setenv("BAIODIGEST_DATA_DIR", str(data_dir))
    monkeypatch.setenv("BAIODIGEST_DOCS_DIR", str(docs_dir))
    monkeypatch.setenv("BAIODIGEST_SITE_URL", "https://example.github.io/baiodigest")
    monkeypatch.setenv("BAIODIGEST_RECIPIENTS_FILE", str(_write_recipients(tmp_path)))

    calls = {}
    monkeypatch.setattr("baiodigest.notify.send_digest_email", lambda **kwargs: calls.update(kwargs))

    notify_for_date("2026-03-08")

    assert calls["subject"] == "[baioDigest] 2026-03-08 digest is live"
    assert "daily/2026-03-08.html" in calls["body"]


def test_notify_for_date_requires_existing_digest_page(monkeypatch, tmp_path) -> None:
    ...
    with pytest.raises(FileNotFoundError):
        notify_for_date("2026-03-08")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_notify.py -v`
Expected: FAIL because `notify.py` and `notify_for_date` do not exist yet.

**Step 3: Write minimal implementation**

Create `src/baiodigest/notify.py`:

```python
def notify_for_date(raw_date: str) -> None:
    settings = get_settings()
    digest_path = settings.data_dir / f"{raw_date}.json"
    daily_path = settings.docs_dir / "daily" / f"{raw_date}.html"
    if not digest_path.exists():
        raise FileNotFoundError(f"Digest JSON not found: {digest_path}")
    if not daily_path.exists():
        raise FileNotFoundError(f"Digest page not found: {daily_path}")
    if not settings.site_url:
        raise ValueError("BAIODIGEST_SITE_URL must be set")

    digest = DailyDigest.from_file(digest_path)
    entry_count = len(digest.entries)
    subject, body = build_digest_email(raw_date, entry_count, settings.site_url)
    send_digest_email(...)


def main() -> int:
    ...
```

Use `argparse` with `--date YYYY-MM-DD`. Default to `date.today().isoformat()` only if that matches the operational policy you want during implementation; otherwise require explicit `--date`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_notify.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/baiodigest/notify.py tests/test_notify.py
git commit -m "feat: add digest notification CLI"
```

### Task 4: Trigger notifications after successful push and document setup

**Files:**
- Modify: `scripts/run-daily.sh`
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Optional Modify: `.gitignore`
- Test: `tests/test_config.py`
- Test: `tests/test_notify.py`

**Step 1: Write the failing test**

Add one more test to `tests/test_notify.py` if needed for the exact date/subject/body behavior that `run-daily.sh` will rely on, such as:

```python
def test_build_digest_email_uses_daily_entry_count_not_stats_fallback() -> None:
    subject, body = build_digest_email(
        digest_date="2026-03-08",
        entry_count=0,
        site_url="https://example.github.io/baiodigest",
    )

    assert "[baioDigest]" in subject
    assert "daily/2026-03-08.html" in body
```

This protects the shell integration from depending on undocumented formatting.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_notify.py -v`
Expected: FAIL if the message contract still needs adjustment.

**Step 3: Write minimal implementation**

Update `scripts/run-daily.sh` so notification only happens on a successful push with actual changes:

```bash
if git -C "$PROJECT_DIR" diff --cached --quiet; then
    echo "[INFO] No changes to commit." >> "$LOG_DIR/daily.log"
else
    TODAY=$(date '+%Y-%m-%d')
    git -C "$PROJECT_DIR" commit -m "digest: $TODAY" >> "$LOG_DIR/daily.log" 2>&1
    git -C "$PROJECT_DIR" push origin main >> "$LOG_DIR/daily.log" 2>&1
    "$UV" run python -m baiodigest.notify --date "$TODAY" >> "$LOG_DIR/daily.log" 2>&1
fi
```

Update docs with:
- required env vars
- Gmail app password setup note
- `recipients.toml.example` usage
- manual notification command:

```bash
uv run python -m baiodigest.notify --date 2026-03-08
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py tests/test_notify.py tests/test_main.py -v`
Expected: PASS

Then run a broader regression pass:

Run: `uv run pytest -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/run-daily.sh README.md CLAUDE.md tests/test_config.py tests/test_notify.py
git commit -m "feat: send digest email after publish"
```
