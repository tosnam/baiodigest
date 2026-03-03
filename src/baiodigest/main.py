from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
import json
import logging
from pathlib import Path

from baiodigest.config import Settings, get_settings
from baiodigest.fetchers import merge_papers
from baiodigest.fetchers.pubmed import PubmedClient
from baiodigest.filters.relevance import filter_papers
from baiodigest.generator.site import StaticSiteGenerator
from baiodigest.models import DailyDigest, DigestEntry, Paper
from baiodigest.summarizer.ollama import OllamaClient

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _existing_digest_dates(data_dir: Path) -> list[date]:
    dates: list[date] = []
    for path in data_dir.glob("*.json"):
        try:
            dates.append(_parse_date(path.stem))
        except ValueError:
            continue
    return sorted(dates)


def _target_dates(data_dir: Path, explicit_date: date | None, max_backfill_days: int = 5) -> list[date]:
    if explicit_date is not None:
        return [explicit_date]

    reference_date = date.today()
    existing = _existing_digest_dates(data_dir)
    if not existing:
        return [reference_date]

    last_collected = existing[-1]
    if last_collected >= reference_date:
        return []

    dates: list[date] = []
    cursor = last_collected + timedelta(days=1)
    while cursor <= reference_date:
        dates.append(cursor)
        cursor += timedelta(days=1)

    if len(dates) > max_backfill_days:
        return dates[-max_backfill_days:]
    return dates


def _pubmed_query_date(digest_date: date) -> date:
    return digest_date - timedelta(days=1)


def _fetch_papers(target: date, settings: Settings) -> tuple[list[Paper], date]:
    query_date = _pubmed_query_date(target)
    with PubmedClient(settings) as pubmed:
        pubmed_papers = pubmed.fetch_papers(query_date, query_date)
    merged = merge_papers([pubmed_papers])

    for paper in merged:
        if not paper.date:
            paper.date = query_date.isoformat()

    return merged, query_date


def _write_raw(target: date, papers: list[Paper], data_dir: Path) -> None:
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{target.isoformat()}.json"
    raw_path.write_text(
        json.dumps([paper.to_dict() for paper in papers], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _run_pipeline_for_date(target: date, force: bool, fetch_only: bool) -> bool:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    digest_path = settings.data_dir / f"{target.isoformat()}.json"
    if digest_path.exists() and not force and not fetch_only:
        logger.info("Digest already exists for %s; skipping", target.isoformat())
        return False

    papers, query_date = _fetch_papers(target, settings)
    logger.info(
        "Collected %d merged papers for digest_date=%s (pubmed_query_date=%s)",
        len(papers),
        target.isoformat(),
        query_date.isoformat(),
    )

    if fetch_only:
        _write_raw(target, papers, settings.data_dir)
        logger.info("Raw fetch output written for %s", target.isoformat())
        return True

    with OllamaClient(settings) as ollama:
        filtered, prefilter_pass_count = filter_papers(papers, settings, ollama)
        entries: list[DigestEntry] = []

        for paper, filter_result in filtered:
            try:
                summary = ollama.summarize(paper.title, paper.abstract)
                entries.append(DigestEntry(paper=paper, filter_result=filter_result, summary=summary))
            except Exception as exc:
                logger.warning("Failed to process paper '%s': %s", paper.title, exc)

    digest = DailyDigest(
        date=target.isoformat(),
        entries=entries,
        stats={
            "collected": len(papers),
            "prefilter_passed": prefilter_pass_count,
            "llm_passed": len(filtered),
            "summarized": len(entries),
        },
    )
    digest.to_file(digest_path)

    logger.info(
        "Finished %s: collected=%d prefilter_passed=%d llm_passed=%d summarized=%d",
        target.isoformat(),
        len(papers),
        prefilter_pass_count,
        len(filtered),
        len(entries),
    )
    return True


def _generate_site() -> None:
    settings = get_settings()
    generator = StaticSiteGenerator(
        template_dir=settings.template_dir,
        static_dir=settings.static_dir,
        data_dir=settings.data_dir,
        docs_dir=settings.docs_dir,
        site_prefix=settings.site_prefix,
    )
    generator.generate()
    logger.info("Static site generated at %s", settings.docs_dir)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="baioDigest pipeline")
    parser.add_argument("--fetch-only", action="store_true", help="Fetch papers only")
    parser.add_argument("--generate-only", action="store_true", help="Generate static site only")
    parser.add_argument("--date", type=_parse_date, help="Target date in YYYY-MM-DD")
    parser.add_argument("--force", action="store_true", help="Re-run even if output exists")
    return parser


def main() -> int:
    _configure_logging()
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.fetch_only and args.generate_only:
        parser.error("--fetch-only and --generate-only cannot be used together")

    if args.generate_only:
        _generate_site()
        return 0

    settings = get_settings()
    targets = _target_dates(settings.data_dir, args.date, max_backfill_days=5)

    if not targets:
        logger.info("No target dates to process")
        if not args.fetch_only:
            _generate_site()
        return 0

    any_processed = False
    for target in targets:
        processed = _run_pipeline_for_date(target, force=args.force, fetch_only=args.fetch_only)
        any_processed = any_processed or processed

    if any_processed and not args.fetch_only:
        _generate_site()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
