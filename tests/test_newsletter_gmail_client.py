from pathlib import Path

from baiodigest.newsletters.gmail_client import extract_html_body
from baiodigest.newsletters.state import NewsletterCheckpoint, load_checkpoint, save_checkpoint


def test_extract_html_body_prefers_html_part() -> None:
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/plain", "body": {"data": "cGxhaW4="}},
            {"mimeType": "text/html", "body": {"data": "PGgxPkhlbGxvPC9oMT4="}},
        ],
    }

    assert extract_html_body(payload) == "<h1>Hello</h1>"


def test_checkpoint_round_trips_json(tmp_path: Path) -> None:
    checkpoint = NewsletterCheckpoint(last_internal_date_ms=1234567890)
    path = tmp_path / "newsletter-state.json"

    save_checkpoint(path, checkpoint)
    loaded = load_checkpoint(path)

    assert loaded.last_internal_date_ms == 1234567890
