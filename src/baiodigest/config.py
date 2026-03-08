from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import tomllib


@dataclass(slots=True, frozen=True)
class SearchQuery:
    name: str
    terms: str
    pubmed_filter: str | None = None


@dataclass(slots=True, frozen=True)
class EmailRecipient:
    email: str


@dataclass(slots=True, frozen=True)
class NewsletterLabel:
    source: str
    gmail_label: str


def _project_root() -> Path:
    default_root = Path(__file__).resolve().parents[2]
    root = Path(os.getenv("BAIODIGEST_ROOT", str(default_root))).expanduser()
    return root.resolve()


def _resolve_path(env_var: str, default_name: str) -> Path:
    root = _project_root()
    raw_value = os.getenv(env_var)
    if raw_value:
        candidate = Path(raw_value).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
        return candidate.resolve()
    return (root / default_name).resolve()


def _resolve_dir(env_var: str, default_name: str) -> Path:
    return _resolve_path(env_var, default_name)


def _normalize_site_prefix(value: str) -> str:
    raw = value.strip()
    if not raw or raw == "/":
        return ""
    if not raw.startswith("/"):
        raw = f"/{raw}"
    return raw.rstrip("/")


def _load_pubmed_queries(path: Path) -> list[SearchQuery]:
    if not path.exists():
        raise ValueError(f"queries.toml not found: {path}")

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise ValueError(f"Failed to parse queries.toml: {path}") from exc

    raw_queries = data.get("queries")
    if not isinstance(raw_queries, list) or not raw_queries:
        raise ValueError("queries.toml must contain a non-empty [[queries]] array")

    loaded: list[SearchQuery] = []
    for idx, item in enumerate(raw_queries, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Query #{idx} must be a table")

        name = str(item.get("name", "")).strip()
        terms = str(item.get("terms", "")).strip()
        if not name or not terms:
            raise ValueError(f"Query #{idx} must define non-empty 'name' and 'terms'")

        raw_filter = item.get("pubmed_filter")
        if raw_filter is None:
            pubmed_filter = None
        else:
            pubmed_filter = str(raw_filter).strip() or None

        loaded.append(SearchQuery(name=name, terms=terms, pubmed_filter=pubmed_filter))

    return loaded


def _load_recipients(path: Path) -> list[EmailRecipient]:
    if not path.exists():
        return []

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise ValueError(f"Failed to parse recipients.toml: {path}") from exc

    raw_recipients = data.get("recipients")
    if not isinstance(raw_recipients, list) or not raw_recipients:
        raise ValueError("recipients.toml must contain a non-empty [[recipients]] array")

    loaded: list[EmailRecipient] = []
    for idx, item in enumerate(raw_recipients, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Recipient #{idx} must be a table")

        email = str(item.get("email", "")).strip()
        if not email:
            raise ValueError(f"Recipient #{idx} must define non-empty 'email'")
        loaded.append(EmailRecipient(email=email))

    return loaded


@dataclass(slots=True)
class Settings:
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3:8b"))
    ollama_timeout_sec: int = field(default_factory=lambda: int(os.getenv("OLLAMA_TIMEOUT_SEC", "120")))
    relevance_threshold: float = field(default_factory=lambda: float(os.getenv("RELEVANCE_THRESHOLD", "0.6")))

    pubmed_base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    exclude_keywords: list[str] = field(
        default_factory=lambda: [
            "clinical trial",
            "case report",
            "meta-analysis",
            "epidemiology",
            "survey",
        ]
    )

    data_dir: Path = field(default_factory=lambda: _resolve_dir("BAIODIGEST_DATA_DIR", "data"))
    newsletter_data_dir: Path = field(
        default_factory=lambda: _resolve_dir("BAIODIGEST_NEWSLETTER_DATA_DIR", "data/newsletters")
    )
    docs_dir: Path = field(default_factory=lambda: _resolve_dir("BAIODIGEST_DOCS_DIR", "docs"))
    template_dir: Path = field(default_factory=lambda: _resolve_dir("BAIODIGEST_TEMPLATE_DIR", "templates"))
    static_dir: Path = field(default_factory=lambda: _resolve_dir("BAIODIGEST_STATIC_DIR", "static"))

    queries_file: Path = field(default_factory=lambda: _resolve_path("BAIODIGEST_QUERIES_FILE", "queries.toml"))
    recipients_file: Path = field(default_factory=lambda: _resolve_path("BAIODIGEST_RECIPIENTS_FILE", "recipients.toml"))
    site_prefix: str = field(
        default_factory=lambda: _normalize_site_prefix(os.getenv("BAIODIGEST_SITE_PREFIX", "/baiodigest"))
    )
    site_url: str = field(default_factory=lambda: os.getenv("BAIODIGEST_SITE_URL", "").rstrip("/"))
    smtp_host: str = field(default_factory=lambda: os.getenv("BAIODIGEST_SMTP_HOST", "smtp.gmail.com"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("BAIODIGEST_SMTP_PORT", "465")))
    smtp_username: str = field(default_factory=lambda: os.getenv("BAIODIGEST_SMTP_USERNAME", ""))
    smtp_app_password: str = field(default_factory=lambda: os.getenv("BAIODIGEST_SMTP_APP_PASSWORD", ""))
    smtp_from_name: str = field(default_factory=lambda: os.getenv("BAIODIGEST_SMTP_FROM_NAME", "baioDigest"))
    gmail_credentials_file: Path = field(
        default_factory=lambda: _resolve_path("BAIODIGEST_GMAIL_CREDENTIALS_FILE", "gmail-credentials.json")
    )
    gmail_token_file: Path = field(
        default_factory=lambda: _resolve_path("BAIODIGEST_GMAIL_TOKEN_FILE", ".secrets/gmail-token.json")
    )
    gmail_nature_label: str = field(
        default_factory=lambda: os.getenv("BAIODIGEST_GMAIL_NATURE_LABEL", "baiodigest/nature")
    )
    gmail_science_label: str = field(
        default_factory=lambda: os.getenv("BAIODIGEST_GMAIL_SCIENCE_LABEL", "baiodigest/science")
    )
    pubmed_queries: list[SearchQuery] = field(init=False)
    email_recipients: list[EmailRecipient] = field(init=False)
    newsletter_labels: list[NewsletterLabel] = field(init=False)

    def __post_init__(self) -> None:
        self.pubmed_queries = _load_pubmed_queries(self.queries_file)
        self.email_recipients = _load_recipients(self.recipients_file)
        self.newsletter_labels = [
            NewsletterLabel(source="nature", gmail_label=self.gmail_nature_label),
            NewsletterLabel(source="science", gmail_label=self.gmail_science_label),
        ]


DEFAULT_SCHEMA_VERSION = "1.0"


def get_settings() -> Settings:
    return Settings()
