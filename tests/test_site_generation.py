from pathlib import Path

from baiodigest.generator.site import StaticSiteGenerator
from baiodigest.models import DailyDigest, DigestEntry, FilterResult, Paper, Summary


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


def test_generate_site_normalizes_english_reason(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")

    entry = DigestEntry(
        paper=Paper(
            title="Test paper",
            abstract="Test abstract",
            authors=["A"],
            affiliations=[],
            doi=None,
            source="pubmed",
            source_type="published",
            journal="Test Journal",
            url="https://example.org",
            category=None,
            date="2026-03-02",
            mesh_terms=[],
        ),
        filter_result=FilterResult(
            relevant=True,
            confidence=0.8,
            category="ai_enzyme",
            reason="This paper is relevant for industry applications.",
            matched_keywords=["enzyme/protein engineering + AI"],
        ),
        summary=Summary(
            background="배경",
            method="방법",
            result="결과",
            significance="의미",
        ),
    )
    digest = DailyDigest(date="2026-03-02", entries=[entry], stats={"collected": 1, "summarized": 1})
    digest.to_file(data_dir / "2026-03-02.json")

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    daily_html = (docs_dir / "daily" / "2026-03-02.html").read_text(encoding="utf-8")

    assert "산업적 활용 가능성이 있어 관련 논문으로 판단했습니다." in daily_html


def test_generate_site_renders_redesigned_index_and_archive(tmp_path) -> None:
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

    assert 'class="site-shell"' in index_html
    assert 'class="hero-summary"' in index_html
    assert "최신 다이제스트" in index_html
    assert 'class="digest-list"' in index_html
    assert 'class="archive-list"' in archive_html
    assert 'class="archive-row"' in archive_html


def test_generate_site_renders_redesigned_daily_digest(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")

    entry = DigestEntry(
        paper=Paper(
            title="Test paper",
            abstract="Test abstract",
            authors=["A"],
            affiliations=["Example Institute"],
            doi=None,
            source="pubmed",
            source_type="published",
            journal="Test Journal",
            url="https://example.org",
            category=None,
            date="2026-03-02",
            mesh_terms=[],
        ),
        filter_result=FilterResult(
            relevant=True,
            confidence=0.8,
            category="ai_enzyme",
            reason="산업적 활용 가능성이 있어 관련 논문으로 판단했습니다.",
            matched_keywords=["enzyme"],
        ),
        summary=Summary(
            background="배경",
            method="방법",
            result="결과",
            significance="의미",
        ),
    )
    digest = DailyDigest(date="2026-03-02", entries=[entry], stats={"collected": 1, "summarized": 1})
    digest.to_file(data_dir / "2026-03-02.json")

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    daily_html = (docs_dir / "daily" / "2026-03-02.html").read_text(encoding="utf-8")

    assert 'class="digest-header"' in daily_html
    assert 'class="paper-card"' in daily_html
    assert 'class="paper-meta"' in daily_html
    assert 'class="summary-grid"' in daily_html
    assert 'class="paper-notes"' in daily_html
