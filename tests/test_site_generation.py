import html
from pathlib import Path

from baiodigest.config import SearchQuery
from baiodigest.generator.site import StaticSiteGenerator
from baiodigest.models import (
    DailyDigest,
    DigestEntry,
    FilterResult,
    NewsletterArticleBriefing,
    NewsletterIssue,
    NewsletterItem,
    NewsletterSection,
    NewsletterSummary,
    Paper,
    Summary,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _write_sample_digest(data_dir: Path) -> None:
    digest = DailyDigest(date="2026-03-02", entries=[], stats={"collected": 1, "summarized": 0})
    digest.to_file(data_dir / "2026-03-02.json")


def _write_sample_digests(data_dir: Path, dates: list[str]) -> None:
    for date in dates:
        digest = DailyDigest(date=date, entries=[], stats={"collected": 1, "summarized": 0})
        digest.to_file(data_dir / f"{date}.json")


def _write_sample_newsletter_issue(
    data_dir: Path,
    source: str,
    message_id: str,
    title: str,
    *,
    newsletter_name: str | None = None,
    sender: str | None = None,
    summary: NewsletterSummary | None = None,
    received_at: str = "2026-03-08T06:30:00+00:00",
    published_at: str = "2026-03-08",
) -> None:
    issue = NewsletterIssue(
        source=source,
        newsletter_name=newsletter_name or ("Nature Briefing" if source == "nature" else "ScienceAdviser"),
        message_id=message_id,
        thread_id=f"thread-{message_id}",
        received_at=received_at,
        published_at=published_at,
        title=title,
        canonical_url=f"https://example.com/{message_id}",
        html_body="<html></html>",
        text_body=title,
        sections=[
            NewsletterSection(
                heading="Top stories",
                items=[NewsletterItem(title=title, url=f"https://example.com/{message_id}", snippet="summary", section_name="Top stories")],
            )
        ],
        summary=summary,
        raw_metadata={"from": sender or f"{newsletter_name or ('Nature Briefing' if source == 'nature' else 'ScienceAdviser')} <news@example.com>"},
    )
    issue.to_file(data_dir / "newsletters" / source / f"{message_id}.json")


def test_index_renders_newsletter_sections_instead_of_archive_preview(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digests(data_dir, ["2026-03-08"])
    _write_sample_newsletter_issue(data_dir, "nature", "nature-1", "Cancer therapy advances")
    _write_sample_newsletter_issue(data_dir, "science", "science-1", "Gene editor improves precision")

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")

    assert "Newsletter Briefings" in index_html
    assert "Archive preview" not in index_html
    assert "Nature" in index_html
    assert "Science" in index_html


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
    _write_sample_digests(
        data_dir,
        [
            "2026-03-01",
            "2026-03-02",
            "2026-03-03",
            "2026-03-04",
            "2026-03-05",
            "2026-03-06",
            "2026-03-07",
            "2026-03-08",
        ],
    )

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

    assert "Bio and AI research digest" in index_html
    assert 'class="site-shell"' in index_html
    assert 'class="hero-summary"' in index_html
    assert 'src="/baiodigest/static/theme.js"' in index_html
    assert "baiodigest-theme" in index_html
    assert 'data-theme-toggle' in index_html
    assert 'class="site-footer-inner"' in index_html
    assert "Research Articles" in index_html
    assert "Today's Digest" not in index_html
    assert "2026-03-08 기준으로 선별한 논문 0편을 정리했습니다." in index_html
    assert "차분한 읽기 흐름으로" not in index_html
    assert '<a class="primary-link" href="/baiodigest/daily/2026-03-08.html">View</a>' in index_html
    assert "최신 다이제스트" not in index_html
    assert "Newsletter Briefings" in index_html
    assert "Archive preview" not in index_html
    assert "<h2>Newsletter Briefings</h2>" in index_html
    assert index_html.count('class="digest-row"') == 1
    assert "아직 수집된 뉴스레터가 없습니다." in index_html
    assert 'class="digest-list"' in index_html
    assert "Built by" in index_html
    assert "@tosnam" in index_html
    assert 'href="https://github.com/tosnam/baiodigest"' in index_html
    assert 'target="_blank"' in index_html
    assert 'rel="noopener noreferrer"' in index_html
    assert 'class="archive-calendar"' in archive_html
    assert 'class="archive-month-grid"' in archive_html


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
    assert 'class="paper-detail-stack"' in daily_html
    assert 'class="paper-notes"' in daily_html


def test_generate_site_renders_queries_page(tmp_path) -> None:
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
        queries=[
            SearchQuery(
                name="enzyme/protein engineering + AI",
                terms='("enzyme engineering" OR "protein engineering") AND ("machine learning")',
                pubmed_filter=None,
            ),
            SearchQuery(
                name="omics + AI (top journals)",
                terms='("omics") AND ("artificial intelligence")',
                pubmed_filter="(Nature[Journal] OR Science[Journal])",
            ),
        ],
    )
    generator.generate()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")
    queries_html = html.unescape((docs_dir / "queries.html").read_text(encoding="utf-8"))

    assert 'href="/baiodigest/queries.html"' in index_html
    assert "<h2>Search Queries</h2>" in queries_html
    assert "enzyme/protein engineering + AI" in queries_html
    assert '("enzyme engineering" OR "protein engineering") AND ("machine learning")' in queries_html
    assert "omics + AI (top journals)" in queries_html
    assert "(Nature[Journal] OR Science[Journal])" in queries_html
    assert "<dt>PubMed filter</dt>" in queries_html
    assert "Built by" in queries_html
    assert "@tosnam" in queries_html
    assert 'href="https://github.com/tosnam/baiodigest"' in queries_html
    assert 'target="_blank"' in queries_html
    assert 'rel="noopener noreferrer"' in queries_html


def test_generate_site_copies_digest_theme_styles(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = _repo_root() / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    _write_sample_digest(data_dir)

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    style_css = (docs_dir / "static" / "style.css").read_text(encoding="utf-8")
    theme_js = (docs_dir / "static" / "theme.js").read_text(encoding="utf-8")

    assert "Noto Sans KR" in style_css
    assert "Noto Serif KR" in style_css
    assert ".hero-summary" in style_css
    assert ".paper-card" in style_css
    assert "font-size: clamp(1.2rem, 2.4vw, 1.6rem);" in style_css
    assert "grid-template-columns: 1fr;" in style_css
    assert "flex-wrap: wrap;" in style_css
    assert "width: auto;" in style_css
    assert "baiodigest-theme" in theme_js
    assert "matchMedia" in theme_js


def test_generate_site_output_has_no_trailing_whitespace(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = _repo_root() / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    _write_sample_digest(data_dir)

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    pages = [
        docs_dir / "index.html",
        docs_dir / "archive.html",
        docs_dir / "daily" / "2026-03-02.html",
    ]

    for page in pages:
        content = page.read_text(encoding="utf-8")
        assert all(not line.endswith(" ") for line in content.splitlines()), page.name


def test_generate_site_renders_monthly_archive_pages(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digests(data_dir, ["2026-02-10", "2026-03-02", "2026-05-20"])

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    latest_archive = (docs_dir / "archive.html").read_text(encoding="utf-8")
    may_archive = (docs_dir / "archive" / "2026-05.html").read_text(encoding="utf-8")
    april_archive = (docs_dir / "archive" / "2026-04.html").read_text(encoding="utf-8")

    assert "2026년 5월" in latest_archive
    assert "2026년 5월" in may_archive
    assert "2026년 4월" in april_archive
    assert 'href="/baiodigest/archive/2026-04.html"' in may_archive
    assert 'href="/baiodigest/archive/2026-06.html"' not in may_archive


def test_generate_site_renders_sunday_first_archive_calendar(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digests(data_dir, ["2026-03-02", "2026-03-07"])

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    archive_html = (docs_dir / "archive.html").read_text(encoding="utf-8")

    assert 'class="archive-calendar"' in archive_html
    assert ">일<" in archive_html
    assert ">월<" in archive_html
    assert ">토<" in archive_html
    assert "0편" in archive_html
    assert 'href="/baiodigest/daily/2026-03-02.html"' in archive_html


def test_generate_site_restores_pre_radar_home_without_weekly_preview(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digests(data_dir, ["2026-03-07", "2026-03-08"])

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")

    assert "최신 주간 요약" not in index_html
    assert "Research radar" not in index_html
    assert "기술 주제" not in index_html


def test_generate_site_renders_simplified_daily_sections(tmp_path) -> None:
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

    assert "왜 읽을 만한가" in daily_html
    assert "배경" in daily_html
    assert "방법" in daily_html
    assert "결과" in daily_html
    assert "활용" in daily_html
    headings = [
        "<h4>왜 읽을 만한가</h4>",
        "<h4>배경</h4>",
        "<h4>방법</h4>",
        "<h4>결과</h4>",
        "<h4>활용</h4>",
    ]
    positions = [daily_html.index(heading) for heading in headings]
    assert positions == sorted(positions)
    assert "<h4>의미</h4>" not in daily_html
    assert "<h4>주의</h4>" not in daily_html
    assert "판정 근거:" not in daily_html
    assert "confidence: 0.80" in daily_html


def test_generate_site_does_not_generate_weekly_pages(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digests(data_dir, ["2026-03-07", "2026-03-08"])

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    assert not (docs_dir / "weekly").exists()


def test_generate_site_copies_archive_calendar_styles(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = _repo_root() / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    _write_sample_digest(data_dir)

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    style_css = (docs_dir / "static" / "style.css").read_text(encoding="utf-8")

    assert ".archive-calendar" in style_css
    assert ".archive-month-grid" in style_css
    assert ".archive-day.is-empty" in style_css


def test_index_renders_one_newsletter_card_per_issue_and_uses_view(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digests(data_dir, ["2026-03-08"])
    _write_sample_newsletter_issue(data_dir, "nature", "nature-1", "Lead story 1", newsletter_name="Nature Briefing")
    _write_sample_newsletter_issue(data_dir, "nature", "nature-2", "Lead story 2", newsletter_name="Nature Briefing: Microbiology")
    _write_sample_newsletter_issue(data_dir, "science", "science-1", "Lead story 3", newsletter_name="ScienceAdviser")

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")

    assert "<h2>Newsletter Briefings</h2>" in index_html
    assert index_html.count('class="digest-row"') == 3
    assert "Nature Briefing: Microbiology" in index_html
    assert "ScienceAdviser" in index_html
    assert 'class="primary-link"' in index_html
    assert "View all" not in index_html


def test_index_prefers_sender_branding_over_issue_subject(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_digests(data_dir, ["2026-03-08"])
    _write_sample_newsletter_issue(
        data_dir,
        "nature",
        "nature-1",
        "How koalas escaped a genetic bottleneck",
        newsletter_name="Nature Briefing: Microbiology",
        sender="Nature Briefing: Microbiology <news@example.com>",
    )

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")

    assert "Nature Briefing: Microbiology" in index_html
    assert "How koalas escaped a genetic bottleneck" not in index_html


def test_newsletter_issue_page_renders_article_briefings_without_summary_block(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")
    _write_sample_newsletter_issue(
        data_dir,
        "nature",
        "nature-1",
        "How koalas escaped a genetic bottleneck",
        newsletter_name="Nature Briefing",
        summary=NewsletterSummary(
            overview="전체 요약",
            highlights=[],
            significance="",
            covered_item_titles=["How koalas escaped a genetic bottleneck"],
            article_briefings=[
                NewsletterArticleBriefing(
                    title="How koalas escaped a genetic bottleneck",
                    url="https://example.com/nature-1",
                    briefing_ko="코알라 개체군은 심한 병목을 겪었지만 유전적 회복 신호를 보였습니다.",
                )
            ],
        ),
    )

    generator = StaticSiteGenerator(
        template_dir=template_dir,
        static_dir=static_dir,
        data_dir=data_dir,
        docs_dir=docs_dir,
        site_prefix="/baiodigest",
    )
    generator.generate()

    html = (docs_dir / "newsletters" / "nature" / "nature-1.html").read_text(encoding="utf-8")

    assert "<h3>요약</h3>" not in html
    assert "Top stories" in html
    assert "How koalas escaped a genetic bottleneck" in html
    assert "코알라 개체군은 심한 병목을 겪었지만 유전적 회복 신호를 보였습니다." in html
    assert 'href="https://example.com/nature-1"' in html
    assert ">원문 링크<" not in html
