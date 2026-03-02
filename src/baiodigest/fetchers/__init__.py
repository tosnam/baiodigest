from __future__ import annotations

from collections.abc import Iterable, Sequence
import hashlib
import re

from baiodigest.models import Paper


def normalize_title(title: str) -> str:
    lowered = title.lower()
    alnum_only = re.sub(r"[^a-z0-9\s]", " ", lowered)
    squashed = re.sub(r"\s+", " ", alnum_only).strip()
    return squashed


def title_hash(title: str) -> str:
    normalized = normalize_title(title)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def dedup_key(paper: Paper) -> str:
    if paper.doi:
        return f"doi::{paper.doi.lower().strip()}"
    return f"title::{title_hash(paper.title)}"


def merge_papers(groups: Iterable[Sequence[Paper]]) -> list[Paper]:
    merged: dict[str, Paper] = {}

    for group in groups:
        for paper in group:
            key = dedup_key(paper)
            existing = merged.get(key)
            if existing is None:
                merged[key] = paper
                continue

            # Prefer published metadata when duplicate entries are merged.
            if existing.source_type == "preprint" and paper.source_type == "published":
                merged[key] = paper

    return list(merged.values())


__all__ = ["dedup_key", "merge_papers", "normalize_title", "title_hash"]
