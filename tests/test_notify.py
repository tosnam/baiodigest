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
