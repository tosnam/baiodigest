from pathlib import Path

from baiodigest.generator.site import StaticSiteGenerator
from baiodigest.models import DailyDigest, DigestEntry, FilterResult, Paper, Summary


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _write_sample_digest(data_dir: Path) -> None:
    digest = DailyDigest(date="2026-03-02", entries=[], stats={"collected": 1, "summarized": 0})
    digest.to_file(data_dir / "2026-03-02.json")


def _write_sample_digests(data_dir: Path, dates: list[str]) -> None:
    for date in dates:
        digest = DailyDigest(date=date, entries=[], stats={"collected": 1, "summarized": 0})
        digest.to_file(data_dir / f"{date}.json")


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
    assert "최신 다이제스트" in index_html
    assert "2026-03-08 기준으로 선별한 논문 0편을 정리했습니다." in index_html
    assert "차분한 읽기 흐름으로" not in index_html
    assert ">다이제스트 보기<" in index_html
    assert index_html.count('class="digest-row"') == 7
    assert "/baiodigest/daily/2026-03-08.html" in index_html
    assert "/baiodigest/daily/2026-03-02.html" in index_html
    assert "/baiodigest/daily/2026-03-01.html" not in index_html
    assert 'class="digest-list"' in index_html
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
    assert 'class="summary-grid"' in daily_html
    assert 'class="paper-notes"' in daily_html


def test_generate_site_renders_research_radar_daily_digest(tmp_path) -> None:
    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    static_dir = tmp_path / "static"
    template_dir = _repo_root() / "templates"

    data_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    (static_dir / "style.css").write_text("body {}", encoding="utf-8")

    entry = DigestEntry(
        paper=Paper(
            title="Research radar paper",
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
            topic_tags=["ai_protein_design", "enzyme_stability"],
            problem_tags=["stability"],
            research_type="method",
            practical_distance="mid_term",
        ),
        summary=Summary(
            background="배경",
            method="방법",
            result="결과",
            significance="의미",
            why_it_matters="효소 최적화 아이디어를 바로 얻을 수 있다.",
            novelty_note="데이터 효율이 높다.",
            application_note="효소 라이브러리 설계에 적용 가능하다.",
            caution_note="실험 검증 범위는 제한적이다.",
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
    assert "효소 최적화 아이디어를 바로 얻을 수 있다." in daily_html
    assert 'class="topic-chip"' in daily_html
    assert 'class="problem-chip"' in daily_html
    assert "연구 성격" in daily_html
    assert "실무 근접도" in daily_html
    assert 'class="daily-topic-group"' in daily_html


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

    assert "Noto Sans KR" in style_css
    assert "Noto Serif KR" in style_css
    assert ".hero-summary" in style_css
    assert ".paper-card" in style_css
    assert "font-size: clamp(1.2rem, 2.4vw, 1.6rem);" in style_css
    assert "grid-template-columns: 1fr;" in style_css
    assert "flex-wrap: wrap;" in style_css
    assert "width: auto;" in style_css


def test_generate_site_copies_research_radar_daily_styles(tmp_path) -> None:
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

    assert ".daily-topic-group" in style_css
    assert ".topic-chip" in style_css
    assert ".paper-radar-grid" in style_css


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
