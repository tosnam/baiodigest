from __future__ import annotations

import base64
from collections.abc import Iterator
from pathlib import Path
from typing import Any


GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def _decode_body(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}").decode("utf-8")


def extract_html_body(payload: dict[str, Any]) -> str | None:
    if payload.get("mimeType") == "text/html":
        body = payload.get("body", {})
        data = body.get("data")
        if isinstance(data, str) and data:
            return _decode_body(data)

    for part in payload.get("parts", []):
        html = extract_html_body(part)
        if html:
            return html

    return None


def extract_text_body(payload: dict[str, Any]) -> str | None:
    if payload.get("mimeType") == "text/plain":
        body = payload.get("body", {})
        data = body.get("data")
        if isinstance(data, str) and data:
            return _decode_body(data)

    for part in payload.get("parts", []):
        text = extract_text_body(part)
        if text:
            return text

    return None


def build_gmail_service(credentials_file: Path, token_file: Path) -> Any:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - exercised after deps are added
        raise RuntimeError("Gmail API dependencies are not installed") from exc

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), [GMAIL_READONLY_SCOPE])

    if creds is None or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), [GMAIL_READONLY_SCOPE])
            creds = flow.run_local_server(port=0)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def list_labeled_message_ids(service: Any, label: str, after_ms: int | None = None) -> list[str]:
    query = None
    if after_ms is not None:
        after_seconds = max(after_ms // 1000, 0)
        query = f"after:{after_seconds}"

    response = (
        service.users()
        .messages()
        .list(userId="me", labelIds=[label], q=query, maxResults=100)
        .execute()
    )
    return [item["id"] for item in response.get("messages", []) if "id" in item]


def iter_labeled_message_ids(service: Any, label: str, after_ms: int | None = None) -> Iterator[str]:
    for message_id in list_labeled_message_ids(service, label=label, after_ms=after_ms):
        yield message_id


def get_message(service: Any, message_id: str) -> dict[str, Any]:
    return service.users().messages().get(userId="me", id=message_id, format="full").execute()
