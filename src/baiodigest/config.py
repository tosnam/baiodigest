from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path


def _project_root() -> Path:
    default_root = Path(__file__).resolve().parents[2]
    root = Path(os.getenv("BAIODIGEST_ROOT", str(default_root))).expanduser()
    return root.resolve()


def _resolve_dir(env_var: str, default_name: str) -> Path:
    root = _project_root()
    raw_value = os.getenv(env_var)
    if raw_value:
        candidate = Path(raw_value).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
        return candidate.resolve()
    return (root / default_name).resolve()


@dataclass(slots=True)
class Settings:
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3:8b"))
    ollama_timeout_sec: int = field(default_factory=lambda: int(os.getenv("OLLAMA_TIMEOUT_SEC", "120")))
    relevance_threshold: float = field(default_factory=lambda: float(os.getenv("RELEVANCE_THRESHOLD", "0.6")))

    pubmed_base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    biorxiv_base_url: str = "https://api.biorxiv.org"

    include_keywords: list[str] = field(
        default_factory=lambda: [
            "protein engineering",
            "metabolic engineering",
            "bioinformatics",
            "enzyme",
            "directed evolution",
            "thermostability",
            "activity",
            "ai",
            "machine learning",
            "synthetic biology",
            "pathway",
            "biocatalyst",
        ]
    )
    exclude_keywords: list[str] = field(
        default_factory=lambda: [
            "clinical trial",
            "case report",
            "meta-analysis",
            "epidemiology",
            "survey",
        ]
    )

    biorxiv_categories: list[str] = field(
        default_factory=lambda: [
            "molecular biology",
            "biochemistry",
            "bioinformatics",
            "synthetic biology",
            "bioengineering",
            "systems biology",
        ]
    )

    pubmed_query: str = field(
        default_factory=lambda: os.getenv(
            "PUBMED_QUERY",
            "(protein engineering OR metabolic engineering OR bioinformatics OR "
            "(enzyme AND (AI OR machine learning)) OR directed evolution)",
        )
    )

    data_dir: Path = field(default_factory=lambda: _resolve_dir("BAIODIGEST_DATA_DIR", "data"))
    docs_dir: Path = field(default_factory=lambda: _resolve_dir("BAIODIGEST_DOCS_DIR", "docs"))
    template_dir: Path = field(default_factory=lambda: _resolve_dir("BAIODIGEST_TEMPLATE_DIR", "templates"))
    static_dir: Path = field(default_factory=lambda: _resolve_dir("BAIODIGEST_STATIC_DIR", "static"))


DEFAULT_SCHEMA_VERSION = "1.0"


def get_settings() -> Settings:
    return Settings()
