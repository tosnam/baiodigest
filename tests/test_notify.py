from pathlib import Path

from baiodigest.config import EmailRecipient
from baiodigest.models import DailyDigest, DigestEntry, FilterResult, Paper, Summary
from baiodigest.notify import notify_for_date
from baiodigest.notifications.email import build_digest_email, send_digest_email


def _write_recipients(tmp_path: Path) -> Path:
    recipients_file = tmp_path / "recipients.toml"
    recipients_file.write_text(
        """
[[recipients]]
email = "reader1@example.com"

[[recipients]]
email = "reader2@example.com"
""".strip(),
        encoding="utf-8",
    )
    return recipients_file


def _entry(idx: int) -> DigestEntry:
    return DigestEntry(
        paper=Paper(
            title=f"Paper {idx}",
            abstract="Abstract",
            authors=["Author"],
            affiliations=["Affiliation"],
            doi=None,
            source="pubmed",
            source_type="published",
            journal="Journal",
            url="https://example.org/paper",
            category=None,
            date="2026-03-08",
        ),
        filter_result=FilterResult(
            relevant=True,
            confidence=0.9,
            category="enzyme",
            reason="Relevant",
        ),
        summary=Summary(
            background="Background",
            method="Method",
            result="Result",
            significance="Significance",
        ),
    )


def test_build_digest_email_includes_digest_links() -> None:
    subject, body = build_digest_email(
        digest_date="2026-03-08",
        entry_count=2,
        site_url="https://example.github.io/baiodigest",
    )

    assert subject == "[baioDigest] 2026-03-08 digest is live"
    assert "2026-03-08" in body
    assert "Included papers: 2" in body
    assert "https://example.github.io/baiodigest/index.html" in body
    assert "https://example.github.io/baiodigest/daily/2026-03-08.html" in body


def test_send_digest_email_uses_smtp_ssl(monkeypatch) -> None:
    sent: dict[str, object] = {}

    class FakeSMTP:
        def __init__(self, host: str, port: int) -> None:
            sent["host"] = host
            sent["port"] = port

        def __enter__(self) -> "FakeSMTP":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def login(self, username: str, password: str) -> None:
            sent["login"] = (username, password)

        def send_message(self, message) -> None:
            sent["message"] = message

    monkeypatch.setattr("baiodigest.notifications.email.smtplib.SMTP_SSL", FakeSMTP)

    send_digest_email(
        smtp_host="smtp.gmail.com",
        smtp_port=465,
        smtp_username="sender@example.com",
        smtp_app_password="app-password",
        from_name="baioDigest",
        recipients=[
            EmailRecipient(email="reader1@example.com"),
            EmailRecipient(email="reader2@example.com"),
        ],
        subject="[baioDigest] 2026-03-08 digest is live",
        body="Digest body",
    )

    assert sent["host"] == "smtp.gmail.com"
    assert sent["port"] == 465
    assert sent["login"] == ("sender@example.com", "app-password")
    message = sent["message"]
    assert message["To"] == "reader1@example.com, reader2@example.com"
    assert message["From"] == "baioDigest <sender@example.com>"
    assert message["Subject"] == "[baioDigest] 2026-03-08 digest is live"


def test_notify_for_date_reads_digest_and_sends_email(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    digest = DailyDigest(date="2026-03-08", entries=[_entry(1), _entry(2)], stats={"summarized": 2})
    digest.to_file(data_dir / "2026-03-08.json")
    (docs_dir / "daily").mkdir(parents=True)
    (docs_dir / "daily" / "2026-03-08.html").write_text("<html></html>", encoding="utf-8")

    monkeypatch.setenv("BAIODIGEST_DATA_DIR", str(data_dir))
    monkeypatch.setenv("BAIODIGEST_DOCS_DIR", str(docs_dir))
    monkeypatch.setenv("BAIODIGEST_SITE_URL", "https://example.github.io/baiodigest")
    monkeypatch.setenv("BAIODIGEST_RECIPIENTS_FILE", str(_write_recipients(tmp_path)))
    monkeypatch.setenv("BAIODIGEST_SMTP_USERNAME", "sender@example.com")
    monkeypatch.setenv("BAIODIGEST_SMTP_APP_PASSWORD", "app-password")

    calls: dict[str, object] = {}

    def fake_send_digest_email(**kwargs) -> None:
        calls.update(kwargs)

    monkeypatch.setattr("baiodigest.notify.send_digest_email", fake_send_digest_email)

    notify_for_date("2026-03-08")

    assert calls["subject"] == "[baioDigest] 2026-03-08 digest is live"
    assert "Included papers: 2" in str(calls["body"])
    assert "daily/2026-03-08.html" in str(calls["body"])
    assert calls["smtp_username"] == "sender@example.com"


def test_notify_for_date_requires_existing_digest_page(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    digest = DailyDigest(date="2026-03-08", entries=[_entry(1)], stats={"summarized": 1})
    digest.to_file(data_dir / "2026-03-08.json")

    monkeypatch.setenv("BAIODIGEST_DATA_DIR", str(data_dir))
    monkeypatch.setenv("BAIODIGEST_DOCS_DIR", str(tmp_path / "docs"))
    monkeypatch.setenv("BAIODIGEST_SITE_URL", "https://example.github.io/baiodigest")
    monkeypatch.setenv("BAIODIGEST_RECIPIENTS_FILE", str(_write_recipients(tmp_path)))

    try:
        notify_for_date("2026-03-08")
        assert False, "Expected FileNotFoundError for missing digest page"
    except FileNotFoundError as exc:
        assert "Digest page not found" in str(exc)
