from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape

from baiodigest.config import SearchQuery
from baiodigest.models import DailyDigest, NewsletterIssue


@dataclass(slots=True)
class SiteContext:
    digests: list[DailyDigest]
    queries: list[SearchQuery]
    newsletter_issues: list[NewsletterIssue]

    @property
    def latest(self) -> DailyDigest | None:
        return self.digests[0] if self.digests else None

    @property
    def recent_newsletter_issues(self) -> list[NewsletterIssue]:
        return self.newsletter_issues

    @property
    def newsletter_groups(self) -> dict[str, list[NewsletterIssue]]:
        groups = {"nature": [], "science": []}
        for issue in self.newsletter_issues:
            groups.setdefault(issue.source, []).append(issue)
        return groups

    @property
    def latest_newsletters(self) -> dict[str, NewsletterIssue | None]:
        return {
            source: issues[0] if issues else None
            for source, issues in self.newsletter_groups.items()
        }


@dataclass(slots=True, frozen=True)
class ArchiveDayCell:
    date: str
    day_number: int
    paper_count: int
    in_current_month: bool
    digest_path: str | None


@dataclass(slots=True, frozen=True)
class ArchiveMonthPage:
    year: int
    month: int
    slug: str
    title_label: str
    previous_month_path: str | None
    next_month_path: str | None
    weekday_labels: list[str]
    weeks: list[list[ArchiveDayCell]]


def _load_digests(data_dir: Path) -> list[DailyDigest]:
    digests: list[DailyDigest] = []
    for path in sorted(data_dir.glob("*.json"), reverse=True):
        try:
            digest = DailyDigest.from_file(path)
            _normalize_reasons_for_render(digest)
            digests.append(digest)
        except Exception:
            continue
    digests.sort(key=lambda item: item.date, reverse=True)
    return digests


def _load_newsletter_issues(newsletter_data_dir: Path) -> list[NewsletterIssue]:
    issues: list[NewsletterIssue] = []
    if not newsletter_data_dir.exists():
        return issues

    for path in sorted(newsletter_data_dir.glob("*/*.json"), reverse=True):
        if path.name.startswith("_"):
            continue
        try:
            issues.append(NewsletterIssue.from_file(path))
        except Exception:
            continue

    issues.sort(
        key=lambda item: (
            item.published_at,
            item.received_at,
            item.generated_at,
            item.message_id,
        ),
        reverse=True,
    )
    return issues


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _contains_hangul(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text))


def _normalize_reason(reason: str, relevant: bool) -> str:
    cleaned = " ".join(reason.split()).strip()
    if cleaned and _contains_hangul(cleaned):
        return cleaned
    if relevant:
        return "산업적 활용 가능성이 있어 관련 논문으로 판단했습니다."
    return "산업적 활용 가능성이 낮아 제외했습니다."


def _normalize_reasons_for_render(digest: DailyDigest) -> None:
    for entry in digest.entries:
        entry.filter_result.reason = _normalize_reason(
            reason=entry.filter_result.reason,
            relevant=entry.filter_result.relevant,
        )


def _source_display_name(source: str) -> str:
    if source == "science":
        return "사이언스"
    if source == "nature":
        return "Nature"
    return source.title()


def _build_site_url(site_prefix: str, path: str) -> str:
    cleaned_path = path.lstrip("/")
    if not cleaned_path:
        return site_prefix or "/"
    if site_prefix:
        return f"{site_prefix}/{cleaned_path}"
    return f"/{cleaned_path}"


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _add_month(value: date, offset: int) -> date:
    month_index = (value.year * 12 + (value.month - 1)) + offset
    year, month_zero_based = divmod(month_index, 12)
    return date(year, month_zero_based + 1, 1)


def _iter_month_starts(start: date, end: date) -> list[date]:
    months: list[date] = []
    current = _month_start(start)
    finish = _month_start(end)
    while current <= finish:
        months.append(current)
        current = _add_month(current, 1)
    return months


def _build_archive_month_pages(digests: list[DailyDigest]) -> list[ArchiveMonthPage]:
    if not digests:
        return []

    digest_by_day = {date.fromisoformat(digest.date): digest for digest in digests}
    month_starts = _iter_month_starts(
        start=min(digest_by_day).replace(day=1),
        end=max(digest_by_day).replace(day=1),
    )
    month_calendar = calendar.Calendar(firstweekday=6)
    weekday_labels = ["일", "월", "화", "수", "목", "금", "토"]
    pages: list[ArchiveMonthPage] = []

    for index, month in enumerate(month_starts):
        weeks: list[list[ArchiveDayCell]] = []
        for week in month_calendar.monthdatescalendar(month.year, month.month):
            cells: list[ArchiveDayCell] = []
            for day_value in week:
                digest = digest_by_day.get(day_value)
                cells.append(
                    ArchiveDayCell(
                        date=day_value.isoformat(),
                        day_number=day_value.day,
                        paper_count=len(digest.entries) if digest else 0,
                        in_current_month=day_value.month == month.month,
                        digest_path=f"daily/{day_value.isoformat()}.html" if digest else None,
                    )
                )
            weeks.append(cells)

        previous_month_path = None
        if index > 0:
            previous_month_path = f"archive/{month_starts[index - 1]:%Y-%m}.html"

        next_month_path = None
        if index < len(month_starts) - 1:
            next_month_path = f"archive/{month_starts[index + 1]:%Y-%m}.html"

        pages.append(
            ArchiveMonthPage(
                year=month.year,
                month=month.month,
                slug=month.strftime("%Y-%m"),
                title_label=f"{month.year}년 {month.month}월",
                previous_month_path=previous_month_path,
                next_month_path=next_month_path,
                weekday_labels=weekday_labels,
                weeks=weeks,
            )
        )

    return pages


class StaticSiteGenerator:
    def __init__(
        self,
        template_dir: Path,
        static_dir: Path,
        data_dir: Path,
        docs_dir: Path,
        site_prefix: str,
        queries: list[SearchQuery] | None = None,
        newsletter_data_dir: Path | None = None,
    ) -> None:
        self.template_dir = template_dir
        self.static_dir = static_dir
        self.data_dir = data_dir
        self.docs_dir = docs_dir
        self.site_prefix = site_prefix
        self.queries = list(queries or [])
        self.newsletter_data_dir = newsletter_data_dir or (data_dir / "newsletters")
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.globals["url_for"] = lambda path: _build_site_url(self.site_prefix, path)
        self.env.globals["source_display_name"] = _source_display_name

    def generate(self) -> None:
        digests = _load_digests(self.data_dir)
        newsletter_issues = _load_newsletter_issues(self.newsletter_data_dir)
        context = SiteContext(digests=digests, queries=self.queries, newsletter_issues=newsletter_issues)

        self.docs_dir.mkdir(parents=True, exist_ok=True)
        weekly_dir = self.docs_dir / "weekly"
        if weekly_dir.exists():
            shutil.rmtree(weekly_dir)
        self._copy_static_assets()

        self._render_archive(context)
        self._render_daily_pages(context)
        self._render_newsletter_pages(context)
        self._render_index(context)
        self._render_queries(context)

    def _render_index(self, context: SiteContext) -> None:
        template = self.env.get_template("index.html")
        output = template.render(
            latest=context.latest,
            digests=context.digests,
            newsletter_issues=context.recent_newsletter_issues,
            title="baioDigest",
        )
        _write(self.docs_dir / "index.html", output)

    def _render_archive(self, context: SiteContext) -> None:
        template = self.env.get_template("archive.html")
        archive_months = _build_archive_month_pages(context.digests)
        archive_dir = self.docs_dir / "archive"
        if archive_dir.exists():
            shutil.rmtree(archive_dir)

        if not archive_months:
            output = template.render(digests=context.digests, month_page=None, title="Archive")
            _write(self.docs_dir / "archive.html", output)
            return

        for month_page in archive_months:
            output = template.render(digests=context.digests, month_page=month_page, title=f"Archive {month_page.slug}")
            _write(archive_dir / f"{month_page.slug}.html", output)

        latest_month = archive_months[-1]
        output = template.render(digests=context.digests, month_page=latest_month, title=f"Archive {latest_month.slug}")
        _write(self.docs_dir / "archive.html", output)

    def _render_queries(self, context: SiteContext) -> None:
        template = self.env.get_template("queries.html")
        output = template.render(queries=context.queries, title="Queries")
        _write(self.docs_dir / "queries.html", output)

    def _render_newsletter_pages(self, context: SiteContext) -> None:
        newsletters_dir = self.docs_dir / "newsletters"
        if newsletters_dir.exists():
            shutil.rmtree(newsletters_dir)

        index_template = self.env.get_template("newsletters.html")
        source_template = self.env.get_template("newsletter_source.html")
        issue_template = self.env.get_template("newsletter_issue.html")

        _write(
            self.docs_dir / "newsletters.html",
            index_template.render(
                newsletter_groups=context.newsletter_groups,
                latest_newsletters=context.latest_newsletters,
                title="Newsletters",
            ),
        )

        for source, issues in context.newsletter_groups.items():
            _write(
                newsletters_dir / f"{source}.html",
                source_template.render(
                    source=source,
                    issues=issues,
                    title=f"{source.title()} Newsletters",
                ),
            )

            for issue in issues:
                _write(
                    newsletters_dir / source / f"{issue.message_id}.html",
                    issue_template.render(
                        issue=issue,
                        title=issue.display_title,
                    ),
                )

    def _render_daily_pages(self, context: SiteContext) -> None:
        template = self.env.get_template("daily.html")
        for digest in context.digests:
            output = template.render(digest=digest, title=f"Digest {digest.date}")
            _write(self.docs_dir / "daily" / f"{digest.date}.html", output)

    def _copy_static_assets(self) -> None:
        target = self.docs_dir / "static"
        if target.exists():
            shutil.rmtree(target)
        if self.static_dir.exists():
            shutil.copytree(self.static_dir, target)
