from __future__ import annotations

from email.message import EmailMessage
import smtplib

from baiodigest.config import EmailRecipient


def build_digest_email(digest_date: str, entry_count: int, site_url: str) -> tuple[str, str]:
    subject = f"[baioDigest] {digest_date} digest is live"
    lines = [
        f"Today's baioDigest for {digest_date} is live.",
        f"Included papers: {entry_count}",
        "",
        f"Home: {site_url}/index.html",
        f"Daily: {site_url}/daily/{digest_date}.html",
    ]
    return subject, "\n".join(lines)


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
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{from_name} <{smtp_username}>"
    message["To"] = ", ".join(recipient.email for recipient in recipients)
    message.set_content(body)

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as client:
        client.login(smtp_username, smtp_app_password)
        client.send_message(message)
