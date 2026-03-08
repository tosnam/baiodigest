from pathlib import Path

from baiodigest.newsletters.gmail_client import extract_html_body, list_labeled_message_ids
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


def test_list_labeled_message_ids_resolves_label_name_to_gmail_label_id() -> None:
    calls: dict[str, object] = {}

    class FakeExecute:
        def __init__(self, payload: dict) -> None:
            self.payload = payload

        def execute(self) -> dict:
            return self.payload

    class FakeLabels:
        def list(self, userId: str) -> FakeExecute:
            assert userId == "me"
            return FakeExecute({"labels": [{"id": "Label_123", "name": "baiodigest/nature"}]})

    class FakeMessages:
        def list(self, **kwargs) -> FakeExecute:
            calls.update(kwargs)
            return FakeExecute({"messages": [{"id": "msg-1"}]})

    class FakeUsers:
        def labels(self) -> FakeLabels:
            return FakeLabels()

        def messages(self) -> FakeMessages:
            return FakeMessages()

    class FakeService:
        def users(self) -> FakeUsers:
            return FakeUsers()

    message_ids = list_labeled_message_ids(FakeService(), label="baiodigest/nature", after_ms=123000)

    assert message_ids == ["msg-1"]
    assert calls["labelIds"] == ["Label_123"]
    assert calls["q"] is None
