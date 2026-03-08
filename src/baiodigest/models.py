from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Literal

from baiodigest.config import DEFAULT_SCHEMA_VERSION


Source = Literal["pubmed"]
NewsletterSource = Literal["nature", "science"]
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
    matched_query_names: list[str] = field(default_factory=list)

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
            matched_query_names=list(data.get("matched_query_names", [])),
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
class NewsletterItem:
    title: str
    url: str
    snippet: str
    section_name: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "NewsletterItem":
        return cls(
            title=data.get("title", ""),
            url=data.get("url", ""),
            snippet=data.get("snippet", ""),
            section_name=data.get("section_name", ""),
        )


@dataclass(slots=True)
class NewsletterSection:
    heading: str
    items: list[NewsletterItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "heading": self.heading,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NewsletterSection":
        return cls(
            heading=data.get("heading", ""),
            items=[NewsletterItem.from_dict(item) for item in data.get("items", [])],
        )


@dataclass(slots=True)
class NewsletterSummary:
    overview: str
    highlights: list[str] = field(default_factory=list)
    significance: str = ""
    covered_item_titles: list[str] = field(default_factory=list)
    article_briefings: list["NewsletterArticleBriefing"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "overview": self.overview,
            "highlights": list(self.highlights),
            "significance": self.significance,
            "covered_item_titles": list(self.covered_item_titles),
            "article_briefings": [item.to_dict() for item in self.article_briefings],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NewsletterSummary":
        return cls(
            overview=data.get("overview", ""),
            highlights=list(data.get("highlights", [])),
            significance=data.get("significance", ""),
            covered_item_titles=list(data.get("covered_item_titles", [])),
            article_briefings=[
                NewsletterArticleBriefing.from_dict(item) for item in data.get("article_briefings", [])
            ],
        )


@dataclass(slots=True)
class NewsletterArticleBriefing:
    title: str
    url: str
    briefing_ko: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "NewsletterArticleBriefing":
        return cls(
            title=data.get("title", ""),
            url=data.get("url", ""),
            briefing_ko=data.get("briefing_ko", ""),
        )


@dataclass(slots=True)
class NewsletterIssue:
    source: NewsletterSource
    newsletter_name: str
    message_id: str
    thread_id: str
    received_at: str
    published_at: str
    title: str
    canonical_url: str
    html_body: str
    text_body: str
    sections: list[NewsletterSection] = field(default_factory=list)
    summary: NewsletterSummary | None = None
    raw_metadata: dict[str, str] = field(default_factory=dict)
    schema_version: str = DEFAULT_SCHEMA_VERSION
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def display_title(self) -> str:
        sender = self.raw_metadata.get("from", "").strip()
        if sender:
            sender_name = sender.split("<", 1)[0].strip().strip('"')
            if sender_name:
                return sender_name
        if self.newsletter_name.strip():
            return self.newsletter_name.strip()
        return self.title.strip()

    @property
    def article_briefings_by_title(self) -> dict[str, NewsletterArticleBriefing]:
        if not self.summary:
            return {}
        return {item.title: item for item in self.summary.article_briefings if item.title}

    @property
    def preview_text(self) -> str:
        if self.summary:
            if self.summary.overview.strip():
                return self.summary.overview.strip()
            for briefing in self.summary.article_briefings:
                if briefing.briefing_ko.strip():
                    return briefing.briefing_ko.strip()
        for section in self.sections:
            for item in section.items:
                if item.snippet.strip():
                    return item.snippet.strip()
        return ""

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "newsletter_name": self.newsletter_name,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "received_at": self.received_at,
            "published_at": self.published_at,
            "title": self.title,
            "canonical_url": self.canonical_url,
            "html_body": self.html_body,
            "text_body": self.text_body,
            "sections": [section.to_dict() for section in self.sections],
            "summary": self.summary.to_dict() if self.summary else None,
            "raw_metadata": self.raw_metadata,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict) -> "NewsletterIssue":
        raw_metadata = data.get("raw_metadata", {})
        return cls(
            source=data.get("source", "nature"),
            newsletter_name=data.get("newsletter_name", ""),
            message_id=data.get("message_id", ""),
            thread_id=data.get("thread_id", ""),
            received_at=data.get("received_at", ""),
            published_at=data.get("published_at", ""),
            title=data.get("title", ""),
            canonical_url=data.get("canonical_url", ""),
            html_body=data.get("html_body", ""),
            text_body=data.get("text_body", ""),
            sections=[NewsletterSection.from_dict(item) for item in data.get("sections", [])],
            summary=NewsletterSummary.from_dict(data["summary"]) if data.get("summary") else None,
            raw_metadata={str(key): str(value) for key, value in raw_metadata.items()},
            schema_version=data.get("schema_version", DEFAULT_SCHEMA_VERSION),
            generated_at=data.get("generated_at", datetime.now(UTC).isoformat()),
        )

    @classmethod
    def from_json(cls, raw: str) -> "NewsletterIssue":
        return cls.from_dict(json.loads(raw))

    @classmethod
    def from_file(cls, path: Path) -> "NewsletterIssue":
        return cls.from_json(path.read_text(encoding="utf-8"))


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
