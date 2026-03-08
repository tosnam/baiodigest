from __future__ import annotations

import argparse
from datetime import datetime
import logging

from baiodigest.config import get_settings
from baiodigest.models import DailyDigest
from baiodigest.notifications.email import build_digest_email, send_digest_email

logger = logging.getLogger(__name__)


def _parse_date(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").date().isoformat()


def notify_for_date(raw_date: str) -> None:
    digest_date = _parse_date(raw_date)
    settings = get_settings()
    digest_path = settings.data_dir / f"{digest_date}.json"
    daily_path = settings.docs_dir / "daily" / f"{digest_date}.html"

    if not digest_path.exists():
        raise FileNotFoundError(f"Digest JSON not found: {digest_path}")
    if not daily_path.exists():
        raise FileNotFoundError(f"Digest page not found: {daily_path}")
    if not settings.site_url:
        raise ValueError("BAIODIGEST_SITE_URL must be set")
    if not settings.email_recipients:
        raise ValueError("No email recipients configured")
    if not settings.smtp_username or not settings.smtp_app_password:
        raise ValueError("SMTP credentials must be configured")

    digest = DailyDigest.from_file(digest_path)
    subject, body = build_digest_email(
        digest_date=digest_date,
        entry_count=len(digest.entries),
        site_url=settings.site_url,
    )
    send_digest_email(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_app_password=settings.smtp_app_password,
        from_name=settings.smtp_from_name,
        recipients=settings.email_recipients,
        subject=subject,
        body=body,
    )
    logger.info("Notification sent for %s to %d recipients", digest_date, len(settings.email_recipients))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send baioDigest notification email")
    parser.add_argument("--date", required=True, help="Digest date in YYYY-MM-DD")
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    args = build_arg_parser().parse_args()
    notify_for_date(args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
