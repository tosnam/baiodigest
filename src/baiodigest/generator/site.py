from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape

from baiodigest.models import DailyDigest


@dataclass(slots=True)
class SiteContext:
    digests: list[DailyDigest]

    @property
    def latest(self) -> DailyDigest | None:
        return self.digests[0] if self.digests else None


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


def _build_site_url(site_prefix: str, path: str) -> str:
    cleaned_path = path.lstrip("/")
    if not cleaned_path:
        return site_prefix or "/"
    if site_prefix:
        return f"{site_prefix}/{cleaned_path}"
    return f"/{cleaned_path}"


class StaticSiteGenerator:
    def __init__(
        self,
        template_dir: Path,
        static_dir: Path,
        data_dir: Path,
        docs_dir: Path,
        site_prefix: str,
    ) -> None:
        self.template_dir = template_dir
        self.static_dir = static_dir
        self.data_dir = data_dir
        self.docs_dir = docs_dir
        self.site_prefix = site_prefix
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.globals["url_for"] = lambda path: _build_site_url(self.site_prefix, path)

    def generate(self) -> None:
        digests = _load_digests(self.data_dir)
        context = SiteContext(digests=digests)

        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self._copy_static_assets()

        self._render_archive(context)
        self._render_daily_pages(context)
        self._render_index(context)

    def _render_index(self, context: SiteContext) -> None:
        template = self.env.get_template("index.html")
        output = template.render(latest=context.latest, digests=context.digests, title="baioDigest")
        _write(self.docs_dir / "index.html", output)

    def _render_archive(self, context: SiteContext) -> None:
        template = self.env.get_template("archive.html")
        output = template.render(digests=context.digests, title="Archive")
        _write(self.docs_dir / "archive.html", output)

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
