from __future__ import annotations

from collections.abc import Iterable
from datetime import date
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from baiodigest.config import Settings
from baiodigest.models import Paper

logger = logging.getLogger(__name__)


def _split_authors(raw_authors: str | None) -> list[str]:
    if not raw_authors:
        return []
    return [name.strip() for name in raw_authors.split(";") if name.strip()]


def parse_biorxiv_collection(collection: Iterable[dict], allowed_categories: set[str]) -> list[Paper]:
    papers: list[Paper] = []
    for item in collection:
        category = (item.get("category") or "").strip().lower()
        if allowed_categories and category not in allowed_categories:
            continue

        doi = (item.get("doi") or "").strip() or None
        abstract = (item.get("abstract") or "").strip()
        if not abstract:
            continue

        title = (item.get("title") or "").strip()
        if not title:
            continue

        pub_date = (item.get("date") or "").strip()
        paper_url = (item.get("biorxiv_url") or "").strip()
        if not paper_url and doi:
            paper_url = f"https://www.biorxiv.org/content/{doi}v1"

        corresponding_institution = (item.get("author_corresponding_institution") or "").strip()
        affiliations = [corresponding_institution] if corresponding_institution else []
        source_id = (item.get("version") or "").strip() or doi

        papers.append(
            Paper(
                title=title,
                abstract=abstract,
                authors=_split_authors(item.get("authors")),
                affiliations=affiliations,
                doi=doi,
                source="biorxiv",
                source_type="preprint",
                journal="bioRxiv",
                url=paper_url,
                category=category or None,
                date=pub_date,
                mesh_terms=[],
                source_id=source_id,
            )
        )
    return papers


class BiorxivClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.Client(timeout=30.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
    def _get(self, path: str) -> dict:
        url = f"{self.settings.biorxiv_base_url}{path}"
        resp = self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    def fetch_papers(self, start: date, end: date) -> list[Paper]:
        cursor = 0
        all_papers: list[Paper] = []
        allowed = {value.lower() for value in self.settings.biorxiv_categories}

        while True:
            path = f"/details/biorxiv/{start.isoformat()}/{end.isoformat()}/{cursor}"
            payload = self._get(path)
            collection = payload.get("collection", [])
            if not collection:
                break

            parsed = parse_biorxiv_collection(collection, allowed)
            all_papers.extend(parsed)

            message = payload.get("messages", [{}])[0]
            total_count = int(message.get("count", len(collection)))
            cursor += len(collection)
            if cursor >= total_count:
                break

        logger.info("Fetched %d bioRxiv papers", len(all_papers))
        return all_papers

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "BiorxivClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
