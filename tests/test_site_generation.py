from pathlib import Path

from baiodigest.generator.site import StaticSiteGenerator
from baiodigest.models import DailyDigest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _write_sample_digest(data_dir: Path) -> None:
    digest = DailyDigest(date="2026-03-02", entries=[], stats={"collected": 1, "summarized": 0})
    digest.to_file(data_dir / "2026-03-02.json")


def test_generate_site_uses_project_prefix(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digest(data_dir)

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")
    archive_html = (docs_dir / "archive.html").read_text(encoding="utf-8")

    assert 'href="/baiodigest/static/style.css"' in index_html
    assert 'href="/baiodigest/index.html"' in index_html
    assert 'href="/baiodigest/daily/2026-03-02.html"' in index_html
    assert 'href="/baiodigest/archive.html"' in archive_html


def test_generate_site_with_root_prefix(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digest(data_dir)

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="",
    )
    generator.generate()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")

    assert 'href="/static/style.css"' in index_html
    assert 'href="/index.html"' in index_html
    assert 'href="/daily/2026-03-02.html"' in index_html
