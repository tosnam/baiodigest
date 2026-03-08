from __future__ import annotations

import argparse
import logging
from pathlib import Path

from baiodigest.config import Settings, get_settings
from baiodigest.models import NewsletterIssue, NewsletterSummary
from baiodigest.newsletters.gmail_client import (
    build_gmail_service,
    extract_html_body,
    extract_text_body,
    get_message,
    iter_labeled_message_ids,
)
from baiodigest.newsletters.parsers import parse_nature_issue, parse_science_issue
from baiodigest.newsletters.state import NewsletterCheckpoint, load_checkpoint, save_checkpoint
from baiodigest.newsletters.summarize import build_newsletter_prompt, summarize_issue_payload
from baiodigest.summarizer.ollama import OllamaClient, _extract_json_block

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def save_issue(issue: NewsletterIssue, base_dir: Path) -> Path:
    path = base_dir / issue.source / f"{issue.message_id}.json"
    issue.to_file(path)
    return path


def _stored_message_ids(base_dir: Path, source: str) -> set[str]:
    source_dir = base_dir / source
    return {path.stem for path in source_dir.glob("*.json")}


def _checkpoint_path(base_dir: Path, source: str) -> Path:
    return base_dir / source / "_state.json"


def _select_parser(source: str):
    if source == "nature":
        return parse_nature_issue
    if source == "science":
        return parse_science_issue
    raise ValueError(f"Unsupported newsletter source: {source}")


def _summarize_issue(issue: NewsletterIssue, ollama: OllamaClient) -> NewsletterIssue:
    prompt = build_newsletter_prompt(issue)
    try:
        raw = ollama._generate(prompt)
        payload = _extract_json_block(raw)
        summary, coverage = summarize_issue_payload(issue, payload)
        issue.summary = summary
        if not coverage.is_complete:
            issue.raw_metadata["summary_status"] = "pending"
            issue.raw_metadata["missing_titles"] = " | ".join(coverage.missing_titles)
        else:
            issue.raw_metadata["summary_status"] = "complete"
    except Exception as exc:
        logger.warning("Newsletter summary failed for %s: %s", issue.message_id, exc)
        issue.summary = NewsletterSummary(overview="", significance="", highlights=[], covered_item_titles=[])
        issue.raw_metadata["summary_status"] = "pending"
    return issue


def _parse_issue_from_message(source: str, message: dict) -> NewsletterIssue:
    payload = message.get("payload", {})
    html_body = extract_html_body(payload) or ""
    text_body = extract_text_body(payload) or ""
    headers = {
        item.get("name", "").lower(): item.get("value", "")
        for item in payload.get("headers", [])
        if isinstance(item, dict)
    }
    subject = headers.get("subject", source.title())
    parser = _select_parser(source)
    issue = parser(
        message_id=message.get("id", ""),
        thread_id=message.get("threadId", ""),
        subject=subject,
        html=html_body or text_body,
    )
    issue.received_at = str(message.get("internalDate", ""))
    issue.raw_metadata.update(
        {
            "from": headers.get("from", ""),
            "subject": subject,
        }
    )
    return issue


def fetch_newsletters(settings: Settings, summarize: bool = True) -> int:
    service = build_gmail_service(settings.gmail_credentials_file, settings.gmail_token_file)
    processed = 0

    with OllamaClient(settings) as ollama:
        for label in settings.newsletter_labels:
            source_dir = settings.newsletter_data_dir / label.source
            checkpoint = load_checkpoint(_checkpoint_path(settings.newsletter_data_dir, label.source))
            existing_ids = _stored_message_ids(settings.newsletter_data_dir, label.source)
            latest_internal_date_ms = checkpoint.last_internal_date_ms

            for message_id in iter_labeled_message_ids(service, label.gmail_label, after_ms=checkpoint.last_internal_date_ms):
                if message_id in existing_ids:
                    continue

                message = get_message(service, message_id)
                issue = _parse_issue_from_message(label.source, message)
                if summarize:
                    issue = _summarize_issue(issue, ollama)
                else:
                    issue.raw_metadata["summary_status"] = "skipped"

                save_issue(issue, settings.newsletter_data_dir)
                processed += 1

                try:
                    latest_internal_date_ms = max(latest_internal_date_ms, int(message.get("internalDate", "0")))
                except ValueError:
                    pass

            save_checkpoint(
                _checkpoint_path(settings.newsletter_data_dir, label.source),
                NewsletterCheckpoint(last_internal_date_ms=latest_internal_date_ms),
            )

    return processed


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch labeled newsletters from Gmail")
    parser.add_argument("--no-summary", action="store_true", help="Skip LLM summarization")
    return parser


def main() -> int:
    _configure_logging()
    args = build_arg_parser().parse_args()
    settings = get_settings()
    count = fetch_newsletters(settings, summarize=not args.no_summary)
    logger.info("Fetched %d newsletter issues", count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
