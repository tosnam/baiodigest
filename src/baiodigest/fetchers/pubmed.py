from __future__ import annotations

from datetime import date
import logging
import re
import time
import xml.etree.ElementTree as ET

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from baiodigest.config import SearchQuery, Settings
from baiodigest.models import Paper

logger = logging.getLogger(__name__)


def _clean_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _node_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return _clean_text("".join(node.itertext()))


def _parse_pub_date(article: ET.Element) -> str:
    year = article.findtext(".//PubDate/Year")
    month = article.findtext(".//PubDate/Month")
    day = article.findtext(".//PubDate/Day")

    if year and month and day:
        month_map = {
            "Jan": "01",
            "Feb": "02",
            "Mar": "03",
            "Apr": "04",
            "May": "05",
            "Jun": "06",
            "Jul": "07",
            "Aug": "08",
            "Sep": "09",
            "Oct": "10",
            "Nov": "11",
            "Dec": "12",
        }
        month_value = month_map.get(month, month.zfill(2) if month.isdigit() else "01")
        return f"{year}-{month_value}-{day.zfill(2)}"

    if year and month:
        month_map = {
            "Jan": "01",
            "Feb": "02",
            "Mar": "03",
            "Apr": "04",
            "May": "05",
            "Jun": "06",
            "Jul": "07",
            "Aug": "08",
            "Sep": "09",
            "Oct": "10",
            "Nov": "11",
            "Dec": "12",
        }
        month_value = month_map.get(month, month.zfill(2) if month.isdigit() else "01")
        return f"{year}-{month_value}-01"

    if year:
        return f"{year}-01-01"

    return ""


def parse_pubmed_xml(xml_text: str) -> list[Paper]:
    root = ET.fromstring(xml_text)
    papers: list[Paper] = []

    for article in root.findall(".//PubmedArticle"):
        title = _node_text(article.find(".//ArticleTitle"))
        if not title:
            continue

        abstract_sections = [_node_text(node) for node in article.findall(".//Abstract/AbstractText")]
        abstract = _clean_text(" ".join(section for section in abstract_sections if section))
        if not abstract:
            continue

        authors: list[str] = []
        affiliations: list[str] = []
        for author in article.findall(".//AuthorList/Author"):
            collective_name = _clean_text(author.findtext("CollectiveName"))
            if collective_name:
                authors.append(collective_name)
            else:
                last_name = _clean_text(author.findtext("LastName"))
                initials = _clean_text(author.findtext("Initials"))
                if last_name:
                    name = f"{last_name} {initials}".strip()
                    authors.append(name)

            for aff_node in author.findall("AffiliationInfo/Affiliation"):
                aff_value = _node_text(aff_node)
                if aff_value:
                    affiliations.append(aff_value)

        pmid = _clean_text(article.findtext(".//PMID"))
        journal = _node_text(article.find(".//Journal/Title")) or None
        mesh_terms = [_node_text(node) for node in article.findall(".//MeshHeadingList/MeshHeading/DescriptorName")]
        mesh_terms = [term for term in mesh_terms if term]

        doi: str | None = None
        for article_id in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
            if article_id.attrib.get("IdType") == "doi":
                doi_value = _node_text(article_id)
                if doi_value:
                    doi = doi_value
                    break

        paper_date = _parse_pub_date(article)
        category = mesh_terms[0].lower() if mesh_terms else None

        papers.append(
            Paper(
                title=title,
                abstract=abstract,
                authors=authors,
                affiliations=affiliations,
                doi=doi,
                source="pubmed",
                source_type="published",
                journal=journal,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                category=category,
                date=paper_date,
                mesh_terms=mesh_terms,
                source_id=pmid or None,
            )
        )

    return papers


class PubmedClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.Client(timeout=30.0)
        self._last_request_at = 0.0
        self.last_query_hit_counts: dict[str, int] = {}
        self.last_id_query_names: dict[str, set[str]] = {}

    def _throttle(self) -> None:
        min_interval = 1 / 3
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
    def _get_json(self, path: str, params: dict[str, str]) -> dict:
        self._throttle()
        url = f"{self.settings.pubmed_base_url}/{path}"
        resp = self.client.get(url, params=params)
        self._last_request_at = time.monotonic()
        resp.raise_for_status()
        return resp.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
    def _get_text(self, path: str, params: dict[str, str]) -> str:
        self._throttle()
        url = f"{self.settings.pubmed_base_url}/{path}"
        resp = self.client.get(url, params=params)
        self._last_request_at = time.monotonic()
        resp.raise_for_status()
        return resp.text

    def _build_search_term(self, query: SearchQuery, start: date, end: date) -> str:
        query_clause = f"({query.terms})"
        if query.pubmed_filter:
            query_clause = f"{query_clause} AND ({query.pubmed_filter})"

        date_clause = f"({start.isoformat()}[Date - Publication] : {end.isoformat()}[Date - Publication])"
        return f"{query_clause} AND {date_clause}"

    def search_ids(self, query: SearchQuery, start: date, end: date) -> list[str]:
        term = self._build_search_term(query, start, end)
        retstart = 0
        retmax = 200
        collected: list[str] = []

        while True:
            payload = self._get_json(
                "esearch.fcgi",
                {
                    "db": "pubmed",
                    "retmode": "json",
                    "retmax": str(retmax),
                    "retstart": str(retstart),
                    "sort": "pub_date",
                    "term": term,
                },
            )

            esearch = payload.get("esearchresult", {})
            raw_count = esearch.get("count", "0")
            try:
                total_count = int(raw_count)
            except (TypeError, ValueError):
                total_count = 0

            page_ids = [str(item) for item in esearch.get("idlist", [])]
            if not page_ids:
                break

            collected.extend(page_ids)
            retstart += len(page_ids)
            if retstart >= total_count:
                break

        return collected

    def collect_ids(self, start: date, end: date) -> list[str]:
        unique_ids: list[str] = []
        seen: set[str] = set()
        self.last_query_hit_counts = {}
        self.last_id_query_names = {}

        for query in self.settings.pubmed_queries:
            ids = self.search_ids(query, start, end)
            self.last_query_hit_counts[query.name] = len(ids)

            for pmid in ids:
                self.last_id_query_names.setdefault(pmid, set()).add(query.name)
                if pmid in seen:
                    continue
                seen.add(pmid)
                unique_ids.append(pmid)

        return unique_ids

    def fetch_papers(self, start: date, end: date) -> list[Paper]:
        ids = self.collect_ids(start, end)
        if not ids:
            logger.info("No PubMed papers matched configured queries")
            return []

        papers: list[Paper] = []
        chunk_size = 100
        for idx in range(0, len(ids), chunk_size):
            chunk = ids[idx : idx + chunk_size]
            xml_text = self._get_text(
                "efetch.fcgi",
                {
                    "db": "pubmed",
                    "retmode": "xml",
                    "id": ",".join(chunk),
                },
            )
            papers.extend(parse_pubmed_xml(xml_text))

        for paper in papers:
            if paper.source_id:
                query_names = self.last_id_query_names.get(paper.source_id, set())
                paper.matched_query_names = sorted(query_names)

        logger.info("Fetched %d PubMed papers (query hits=%s)", len(papers), self.last_query_hit_counts)
        return papers

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "PubmedClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
