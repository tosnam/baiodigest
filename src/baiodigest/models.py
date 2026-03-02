from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Literal

from baiodigest.config import DEFAULT_SCHEMA_VERSION


Source = Literal["pubmed", "biorxiv"]
SourceType = Literal["preprint", "published"]


@dataclass(slots=True)
class Paper:
    title: str
    abstract: str
    authors: list[str]
    affiliations: list[str]
    doi: str | None
    source: Source
    source_type: SourceType
    journal: str | None
    url: str
    category: str | None
    date: str
    mesh_terms: list[str] = field(default_factory=list)
    source_id: str | None = None

    def preferred_affiliation(self) -> str | None:
        if self.affiliations:
            return self.affiliations[-1]
        return None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        return cls(
            title=data.get("title", ""),
            abstract=data.get("abstract", ""),
            authors=list(data.get("authors", [])),
            affiliations=list(data.get("affiliations", [])),
            doi=data.get("doi"),
            source=data.get("source", "pubmed"),
            source_type=data.get("source_type", "published"),
            journal=data.get("journal"),
            url=data.get("url", ""),
            category=data.get("category"),
            date=data.get("date", ""),
            mesh_terms=list(data.get("mesh_terms", [])),
            source_id=data.get("source_id"),
        )


@dataclass(slots=True)
class FilterResult:
    relevant: bool
    confidence: float
    category: str
    reason: str
    matched_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FilterResult":
        return cls(
            relevant=bool(data.get("relevant", False)),
            confidence=float(data.get("confidence", 0.0)),
            category=data.get("category", "unknown"),
            reason=data.get("reason", ""),
            matched_keywords=list(data.get("matched_keywords", [])),
        )


@dataclass(slots=True)
class Summary:
    background: str
    method: str
    result: str
    significance: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Summary":
        return cls(
            background=data.get("background", ""),
            method=data.get("method", ""),
            result=data.get("result", ""),
            significance=data.get("significance", ""),
        )


@dataclass(slots=True)
class DigestEntry:
    paper: Paper
    filter_result: FilterResult
    summary: Summary

    def to_dict(self) -> dict:
        return {
            "paper": self.paper.to_dict(),
            "filter_result": self.filter_result.to_dict(),
            "summary": self.summary.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DigestEntry":
        return cls(
            paper=Paper.from_dict(data.get("paper", {})),
            filter_result=FilterResult.from_dict(data.get("filter_result", {})),
            summary=Summary.from_dict(data.get("summary", {})),
        )


@dataclass(slots=True)
class DailyDigest:
    date: str
    entries: list[DigestEntry] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)
    schema_version: str = DEFAULT_SCHEMA_VERSION
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "entries": [entry.to_dict() for entry in self.entries],
            "stats": self.stats,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict) -> "DailyDigest":
        return cls(
            date=data.get("date", ""),
            entries=[DigestEntry.from_dict(item) for item in data.get("entries", [])],
            stats={k: int(v) for k, v in data.get("stats", {}).items()},
            schema_version=data.get("schema_version", DEFAULT_SCHEMA_VERSION),
            generated_at=data.get("generated_at", datetime.now(UTC).isoformat()),
        )

    @classmethod
    def from_json(cls, raw: str) -> "DailyDigest":
        return cls.from_dict(json.loads(raw))

    @classmethod
    def from_file(cls, path: Path) -> "DailyDigest":
        return cls.from_json(path.read_text(encoding="utf-8"))
